#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Plot flux graphs."""
import numpy as np
from astropy import log
from astropy.time import Time
import copy

import config
import graph

############
# CONSTANTS
############
DEFAULT_MIN_METEORS = 100  # meteors
DEFAULT_MIN_ECA = 50000    # km^2 h
DEFAULT_GAMMA = 1.5
DEFAULT_POPINDEX = 2.2     # population index

##########
# CLASSES
#########

class BaseProfile(object):
    """Abstract base class."""

    def __init__(self, fluxdb):
        self.fluxdb = fluxdb

    def field(self, key):
        """Returns a data field"""
        return np.array([row[key] for row in self.fluxes])

    def get_response(self):
        """Returns the flux profile in JSON format.

        Returns
        -------
        dict
        """
        result = {}
        if self.fluxes is None or len(self.fluxes) == 0:
            log.error('No suitable data found.')
            result['status'] = 'WARNING'
            result['msg'] = 'No suitable data found.'
        else:
            result['status'] = 'OK'
            result['graph'] = self.save_graph()
            result['flux'] = []
            for row in self.fluxes:
                newrow = []
                # Averaged profiles do not have a time field
                if row['time']:
                    newrow.append(str(row['time'])[0:16])
                newrow.extend(('{:.3f}'.format(row['solarlon']),
                              '{:.1f}'.format(row['teff']),
                              '{:.1f}'.format(row['eca']),
                              '{0}'.format(row['met']),
                              '{:.1f} &pm; {:.1f}'.format(row['flux'], row['e_flux']),
                              '{:.0f}'.format(row['zhr'])))
                result['flux'].append(newrow)
        return result

    def save_graph(self):
        """Creates a graph and returns the filename.
        """
        mygraph = self.graph()
        return mygraph.save()


class VideoProfile(BaseProfile):

    def __init__(self, fluxdb,
                 shower, start, stop,
                 min_interval=1, max_interval=24,
                 min_meteors=DEFAULT_MIN_METEORS,
                 min_eca=DEFAULT_MIN_ECA, 
                 min_alt=10, min_eca_station=0.5,
                 gamma=DEFAULT_GAMMA,
                 popindex=DEFAULT_POPINDEX):
        """

        Parameters
        ----------
        shower : string
            IMO shower code

        start : string
            ISO timestamp

        stop : string
            ISO timestamp

        min_meteors : int
            Minimum number of meteors in each bin.

        min_eca : float [10^3 km^2 h]
            Minimum ECA in each bin.

        min_interval : float [hours]

        max_interval : float [hours]

        min_alt : float [degrees]
            Minimum radiant altitude for a flux record to be included.

        min_eca_station : float [degrees]
            Minimum ECA for a flux record to be included.

        gamma : float
            Zenith correction exponent.

        popindex : float
            Population index.

        Returns
        -------
        Result of the query.
        """
        BaseProfile.__init__(self, fluxdb)

        if isinstance(start, Time):
            self.start = start
        else:
            self.start = Time(start, scale='utc')

        if isinstance(stop, Time):
            self.stop = stop
        else:
            self.stop = Time(stop, scale='utc')

        self.popindex = popindex
        self.gamma = gamma
        self.fluxes = self.fluxdb.query("""SELECT * FROM
                                    VideoProfile(%s,
                                                 %s::timestamp,
                                                 %s::timestamp,
                                                 %s, %s,
                                                 '%s hours'::interval,
                                                 '%s hours'::interval,
                                                 %s, %s, %s, %s)
                                """, (shower, 
                                      self.start.isot, 
                                      self.stop.isot,
                                      min_meteors, min_eca,
                                      min_interval, max_interval,
                                      min_alt, min_eca_station,
                                      gamma, popindex, ))


    def graph(self):
        mygraph = graph.VideoGraph(self)
        mygraph.plot()
        return mygraph





class SolVideoProfile(BaseProfile):

    def __init__(self, fluxdb, shower,
                 year, start, stop, 
                 min_interval=1, max_interval=24,
                 min_meteors=DEFAULT_MIN_METEORS,
                 min_eca=DEFAULT_MIN_ECA, 
                 min_alt=10, min_eca_station=0.5,
                 gamma=DEFAULT_GAMMA,
                 popindex=DEFAULT_POPINDEX,
                 label=None,
                 marker='s'):
        """

        Parameters
        ----------
        shower : string
            IMO shower code

        years : int
            e.g. 2012

        start : float [degrees]
            Solar longitude.

        stop : float [degrees]
            Solar longitude.

        min_meteors : int
            Minimum number of meteors in each bin.

        min_eca : float [10^3 km^2 h]
            Minimum ECA in each bin.

        min_interval : float [hours]

        max_interval : float [hours]

        min_alt : float [degrees]
            Minimum radiant altitude for a flux record to be included.

        min_eca_station : float [degrees]
            Minimum ECA for a flux record to be included.

        gamma : float
            Zenith correction exponent.

        popindex : float
            Population index.

        Returns
        -------
        Result of the query.
        """
        BaseProfile.__init__(self, fluxdb)
        self.shower = shower
        self.year = year
        self.start = start
        self.stop = stop
        self.popindex = popindex
        self.gamma = gamma
        if label != None:
            self.label = label
        else:
            #self.label = '{0} {1}'.format(shower, year)
            self.label = str(year)
        self.marker = marker
        self.fluxes = self.fluxdb.query("""SELECT * FROM
                                    SolVideoProfile(%s,
                                                 %s, %s, %s,
                                                 %s, %s,
                                                 %s, %s,
                                                 %s, %s, %s, %s)
                                """, (shower, 
                                      year, start, stop,
                                      min_meteors, min_eca,
                                      min_interval, max_interval,
                                      min_alt, min_eca_station,
                                      gamma, popindex, ))


    def graph(self):
        mygraph = graph.SolVideoGraph(self)
        mygraph.plot()
        return mygraph




class AvgVideoProfile(BaseProfile):

    def __init__(self, fluxdb, shower,
                 years, start, stop, 
                 min_interval=1, max_interval=24,
                 min_meteors=DEFAULT_MIN_METEORS,
                 min_eca=DEFAULT_MIN_ECA, 
                 min_alt=10, min_eca_station=0.5,
                 gamma=DEFAULT_GAMMA,
                 popindex=DEFAULT_POPINDEX,
                 label=None,
                 marker='s'):
        """

        Parameters
        ----------
        shower : string
            IMO shower code

        years : list
            e.g. [2011,2012]

        start : float [degrees]
            Solar longitude.

        stop : float [degrees]
            Solar longitude.

        min_meteors : int
            Minimum number of meteors in each bin.

        min_eca : float [10^3 km^2 h]
            Minimum ECA in each bin.

        min_interval : float [hours]

        max_interval : float [hours]

        min_alt : float [degrees]
            Minimum radiant altitude for a flux record to be included.

        min_eca_station : float [degrees]
            Minimum ECA for a flux record to be included.

        gamma : float
            Zenith correction exponent.

        popindex : float
            Population index.

        Returns
        -------
        Result of the query.
        """
        BaseProfile.__init__(self, fluxdb)
        self.shower = shower
        self.years = years
        self.start = start
        self.stop = stop
        self.popindex = popindex
        self.gamma = gamma
        if label != None:
            self.label = label
        elif len(years) == 1:
            self.label = years[0]
        else:
            #self.label = '{0} {1}'.format(shower, year)
            self.label = shower
        self.marker = marker
        self.fluxes = self.fluxdb.query("""SELECT * FROM
                                    AvgVideoProfile(%s,
                                                 %s::int[], %s, %s,
                                                 %s, %s,
                                                 %s, %s,
                                                 %s, %s, %s, %s)
                                """, (shower, 
                                      years, start, stop,
                                      min_meteors, min_eca,
                                      min_interval, max_interval,
                                      min_alt, min_eca_station,
                                      gamma, popindex, ))


    def graph(self):
        mygraph = graph.SolVideoGraph(self)
        mygraph.plot()
        return mygraph
