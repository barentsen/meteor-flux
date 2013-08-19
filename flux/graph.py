#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Plot flux graphs."""
import numpy as np
import matplotlib as mpl
mpl.use('Agg')  # Avoid needing X
import matplotlib.pyplot as plt
import datetime
import tempfile
from astropy import log
from astropy.time import Time
import os

import config
import util

params = {'backend': 'Agg',
          'axes.labelsize': 18,
          'text.fontsize': 16,
          'legend.fontsize': 16,
          'xtick.labelsize': 14,
          'xtick.major.size': 8,
          'xtick.minor.size': 4,
          'ytick.labelsize': 14,
          'figure.figsize': (11,6)}
plt.rcParams.update(params)
#plt.rcParams['axes.facecolor'] = 'F0F0F0'
#plt.rcParams['axes.edgecolor'] = 'E7E7E7'
plt.rcParams['axes.color_cycle'] = ['C5000B', '0084D1', '008000', 'FFD320']


class BaseGraph(object):

    def __init__(self):
        self.fig = plt.figure(dpi=config.DPI) # 11*80 = 880 pixels wide!
        self.fig.subplots_adjust(0.1,0.17,0.92,0.87)

    def show(self):
        self.fig.show()        
        
    def save(self, prefix='flux', format='png', dpi=config.DPI,
             tmpdir=config.TMPDIR, web=True):
        myfile = tempfile.NamedTemporaryFile(prefix=prefix,
                                             suffix='.'+format,
                                             dir=tmpdir,
                                             delete=False)
        self.fig.savefig(myfile, format=format, dpi=dpi)
        
        myfile2 = myfile.name.replace('png', 'pdf')
        self.fig.savefig(myfile2, format='pdf', dpi=dpi)

        if web:
            return config.TMPDIR_WWW+'/'+os.path.basename(myfile.name)
            myfile.close()
            plt.close()
        else:
            return myfile

    ######################
    # LABEL FORMATTER FUNCTIONS
    ######################

    def sollon_formatter(self, a, b):
        """
        a: ordinal datetime
        b: tick nr 
        Usage: ax.xaxis.set_major_formatter(pylab.FuncFormatter(sollon_formatter)) 
        """
        # 10 days
        if self.timespan > 10*24*3600:
            fmt = "%.1f"
        # 1 day
        elif self.timespan > 24*3600:
            fmt = "%.2f"
        else:
            fmt = "%.3f"
        d = datetime.datetime.fromordinal(int(a))+datetime.timedelta(a-int(a))
        return fmt % util.sollon(d)

    def date_formatter(self, a, b):
        """
        a: ordinal datetime
        b: tick nr 
        Usage: ax.xaxis.set_major_formatter(pylab.FuncFormatter(sollon_formatter)) 
        """
        d = datetime.datetime.fromordinal(int(a))+datetime.timedelta(a-int(a))
        if self.timespan > 56:
            fmt = '%d %b'
        else:
            fmt = '%H:%M\n(%d %b)'
        
        return d.strftime(fmt)

    def zhr_formatter(self, a, b):
        zhr = util.flux2zhr(a, self.get_popindex())
        if round(zhr) < 10:
            return "%.1f" % zhr
        else:
            return "%.0f" % zhr

    def get_popindex(self):
        return self.profile.popindex



class VideoGraph(BaseGraph):
    """Graph with a time axis at the bottom and a sollon axis at top."""

    def __init__(self, profile, ymax=None):
        BaseGraph.__init__(self)
        self.profile = profile
        self.timespan = (self.profile.stop - self.profile.start).sec / 3600. # hours
        self.ymax = ymax

    
    def plot(self):
        self.setup_axes()

        self.ax.errorbar(self.profile.field('time'),
                         self.profile.field('flux'),
                         yerr=self.profile.field('e_flux'),
                         fmt="s", ms=4, lw=1.0, c='red')
        
        self.setup_limits()
        self.setup_time_axes()
        self.setup_labels()
       

    def setup_axes(self):
        self.ax = plt.subplot(111)

        # Second Y axis on the right for the ZHR 
        self.ax_zhr = plt.twinx(ax=self.ax)
        self.ax_zhr.set_ylabel("ZHR (r={0:.1f}, $\gamma$={1:.2f})".format(
                                                self.profile.popindex,
                                                self.profile.gamma))
        self.ax_zhr.yaxis.set_major_formatter(plt.FuncFormatter(self.zhr_formatter))
        
        # Second X axis as top for the solar longitude
        self.ax2 = plt.twiny(ax=self.ax)
        self.ax2.set_xlabel("Solar longitude (J2000.0)")
        self.ax2.xaxis.set_major_formatter(plt.FuncFormatter(self.sollon_formatter))
          
        self.ax.grid(which="both")

    def setup_limits(self):
        self.ax.set_xlim([self.profile.start.datetime, self.profile.stop.datetime])
        self.ax2.set_xlim([self.profile.start.datetime, self.profile.stop.datetime])
        self.ax_zhr.set_xlim([self.profile.start.datetime, self.profile.stop.datetime])

        flux = self.profile.field('flux')
        e_flux = self.profile.field('e_flux')
        # Determine the limit of the Y axis
        if self.ymax:
            my_ymax = self.ymax
        elif len(flux) == 0:
            my_ymax = 100
        else:
            my_ymax = 1.1*max(flux+e_flux)

        self.ax.set_ylim([0, my_ymax])
        self.ax2.set_ylim([0, my_ymax])
        self.ax_zhr.set_ylim([0, my_ymax])      


    def setup_time_axes(self):
        if self.timespan > 90*24: # 90 days
            # More than 5 days: only show dates
            majorLocator = mpl.dates.AutoDateLocator(maxticks=10)
            sollonLocator = majorLocator
            majorFormatter = mpl.dates.DateFormatter('%d %b')
            self.xlabel = "Date (UT, %s)" % self.profile.start.datetime.year   
                    
        elif self.timespan > 5*24: # 5 days
            # More than 5 days: only show dates
            majorLocator = mpl.dates.AutoDateLocator(maxticks=10)
            sollonLocator = majorLocator
            majorFormatter = mpl.dates.DateFormatter('%d %b')
            self.xlabel = "Date (UT, %s)" % self.profile.start.datetime.year   
        
        elif self.timespan > 1*24:
            # Between 1 and 5 days: show hours
            majorLocator = mpl.dates.HourLocator(byhour=[0])
            majorFormatter = mpl.dates.DateFormatter('%d %b')
            
            if self.timespan > 3*24:
                t = 12
            elif self.timespan > 1.5*24:
                t = 6
            else:
                t = 3
            byhour = np.arange(t, 24, t)
            
            minorLocator = mpl.dates.HourLocator(byhour=byhour)
            self.ax.xaxis.set_minor_locator(minorLocator)
            sollonLocator = mpl.dates.HourLocator(byhour=np.append(0, byhour))
            fmt2 = mpl.dates.DateFormatter('%H:%M')        
            self.ax.xaxis.set_minor_formatter(plt.FuncFormatter(fmt2))
            self.xlabel = "Date (UT, %s)" % self.profile.start.datetime.year   
            
        else:
            if self.timespan > 18:
                majorLocator = mpl.dates.HourLocator( np.arange(0, 24, 3) ) 
                minorLocator = mpl.dates.HourLocator( np.arange(0, 24, 1) ) 
            elif self.timespan > 12:
                majorLocator = mpl.dates.HourLocator( np.arange(0, 24, 2) ) 
                minorLocator = mpl.dates.HourLocator( np.arange(1, 24, 2) ) 
            elif self.timespan > 6:
                majorLocator = mpl.dates.HourLocator( np.arange(0, 24, 1) ) 
                minorLocator = mpl.dates.MinuteLocator(  np.arange(0,60,30)  )
            elif self.timespan > 3:
                majorLocator = mpl.dates.MinuteLocator(  np.arange(0,60,30)  )
                minorLocator = mpl.dates.MinuteLocator(  np.arange(0,60,15)  )
            elif self.timespan > 1:
                majorLocator = mpl.dates.MinuteLocator( np.arange(0,60,15) ) 
                minorLocator = mpl.dates.MinuteLocator(  np.arange(0,60,5) )
            else:
                majorLocator = mpl.dates.MinuteLocator( np.arange(0,60,10) ) 
                minorLocator = mpl.dates.MinuteLocator(  np.arange(0,60,2) )
                
            
            majorFormatter = mpl.dates.DateFormatter('%H:%M')  
            self.ax.xaxis.set_minor_locator(minorLocator)
            sollonLocator = majorLocator
            self.xlabel = "Time (UT, %s)" % self.profile.start.datetime.strftime('%d %b %Y')
        
        self.ax.xaxis.set_major_formatter(plt.FuncFormatter(majorFormatter))    
        self.ax2.xaxis.set_major_locator(sollonLocator)
        self.ax.xaxis.set_major_locator(majorLocator)


    def setup_labels(self):
        self.ax.set_ylabel("Meteoroids / 1000$\cdot$km$^{2}\cdot$h")
        self.ax.set_xlabel(self.xlabel)
        
        labels = self.ax.get_xmajorticklabels()
        plt.setp(labels, rotation=45) 
        labels = self.ax.get_xminorticklabels()
        plt.setp(labels, rotation=45)





class SolVideoGraph(BaseGraph):
    """Graph with a time axis at the bottom and a sollon axis at top."""

    def __init__(self, profiles, ymax=None):
        """
        Parameters
        ----------
        profiles : FluxProfile or list of FluxProfiles
        """
        BaseGraph.__init__(self)
        
        # Profile can be a list or a single instance
        if isinstance(profiles, (list)):
            self.profiles = profiles
        else:
            self.profiles = [profiles]       

        self.timespan = (self.profiles[0].stop - self.profiles[0].start) # hours
        self.ymax = ymax

    
    def plot(self):
        self.setup_axes()

        for p in self.profiles:
            self.ax.errorbar(p.field('solarlon'),
                             p.field('flux'),
                             yerr=p.field('e_flux'),
                             fmt="s", ms=4, lw=1.0,
                             label=p.label)
        
        if len(self.profiles) > 1:
            self.ax.legend()

        self.setup_limits()
        self.setup_labels()
       

    def setup_axes(self):
        self.ax = plt.subplot(111)
        
        # Second Y axis on the right for the ZHR 
        self.ax_zhr = plt.twinx(ax=self.ax)
        self.ax_zhr.set_ylabel("ZHR (r={0:.1f}, $\gamma$={1:.2f})".format(
                                                self.profiles[0].popindex,
                                                self.profiles[0].gamma))
        self.ax_zhr.yaxis.set_major_formatter(plt.FuncFormatter(self.zhr_formatter))
                       
        self.ax.grid(which="both")

    def setup_limits(self):
        self.ax.set_xlim([self.profiles[0].start, self.profiles[0].stop])
        self.ax_zhr.set_xlim([self.profiles[0].start, self.profiles[0].stop])

        flux = np.concatenate([p.field('flux') for p in self.profiles])
        e_flux = np.concatenate([p.field('e_flux') for p in self.profiles])

        # Determine the limit of the Y axis
        if self.ymax:
            my_ymax = self.ymax
        elif len(flux) == 0:
            my_ymax = 100
        else:
            my_ymax = 1.1*max(flux+e_flux)

        self.ax.set_ylim([0, my_ymax])
        self.ax_zhr.set_ylim([0, my_ymax])      


    def setup_labels(self):
        self.ax.set_ylabel("Meteoroids / 1000$\cdot$km$^{2}\cdot$h")
        self.ax.set_xlabel("Solar longitude (J2000.0)")
                
        #labels = self.ax.get_xmajorticklabels()
        #plt.setp(labels, rotation=45, fontsize=14) 
        #labels = self.ax.get_xminorticklabels()
        #plt.setp(labels, rotation=45, fontsize=12)

    def get_popindex(self):
        return self.profiles[0].popindex