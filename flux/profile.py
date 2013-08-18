#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Plot flux graphs."""
import numpy as np
from astropy import log
from astropy.time import Time

import graph


class BaseProfile(object):
    """Abstract base class."""

    def __init__(self, fluxdb):
        self.fluxdb = fluxdb

    def field(self, key):
        """Returns a data field"""
        return np.array([row[key] for row in self.fluxes])

    def get_json(self):
        """Returns the flux profile in JSON format.

        Returns
        -------
        json : str
        """
        graph_filename = self.save_graph()
        if self.fluxes is None or len(self.fluxes) == 0:
            log.error('Could not find fluxes')
            json = '{"status":"ERROR"}'
        else:
            json = '{{"status":"OK", "graph":"{0}", "flux": ['.format(graph_filename)
            for i, row in enumerate(self.fluxes):
                if i > 0:
                    json += ', \n'
                json += '{'
                json += '"time":"{0}", '.format(str(row['time'])[0:16])
                json += '"sollon":{0:.3f}, '.format(row['solarlon'])
                json += '"teff":{0:.1f}, '.format(row['teff'])
                json += '"eca":{0:.1f}, '.format(row['eca'])
                json += '"met":{0}, '.format(row['met'])
                json += '"flux":{0:.1f}, '.format(row['flux'])
                json += '"e_flux":{0:.1f}, '.format(row['e_flux'])
                json += '"zhr":{0:.0f}'.format(row['zhr'])
                json += '}'
            json += ']}'        
        return json

    def save_graph(self):
        """Creates a graph and returns the filename.
        """
        mygraph = self.graph()
        return mygraph.save()


class VideoProfile(BaseProfile):

    def __init__(self, fluxdb,
                 shower, start, stop,
                 min_interval=1, max_interval=24,
                 min_meteors=20, min_eca=20, 
                 min_alt=10, min_eca_station=0.5,
                 gamma=1.5, popindex=2.0):
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

        self.start = Time(start, scale='utc')
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
                                      start, 
                                      stop,
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
                 years, start, stop, 
                 min_interval=1, max_interval=24,
                 min_meteors=20, min_eca=25000., 
                 min_alt=10, min_eca_station=0.5,
                 gamma=1.5, popindex=2.0,
                 label=None):
        """

        Parameters
        ----------
        shower : string
            IMO shower code

        years : list
            e.g. [2012]

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
        self.years = years
        self.start = start
        self.stop = stop
        self.popindex = popindex
        self.gamma = gamma
        if label != None:
            self.label = label
        else:
            self.label = shower
        self.fluxes = self.fluxdb.query("""SELECT * FROM
                                    AvgVideoProfile(%s,
                                                 %s, %s, %s,
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
