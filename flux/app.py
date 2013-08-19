#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Flask app.

API end-points:

/api/metrecdata
POST -- zip files containing MetRec-formatted data

/api/flux
GET, parameters:
shower -- code
begin -- UT
end -- UT
gamma -- 
binning -- TBD

Returns
-------
JSON objects with flux data and link to graph.
"""
from flask import Flask, request, json
from flux import db, profile, graph, util
from astropy import log, time

fluxapp = Flask('flux', static_url_path='')
MYDB = db.FluxDB()


@fluxapp.route('/api/flux', methods=['GET'])
@util.crossdomain(origin='*')
def flux():
    """Returns flux data.

    Example
    -------
    http://localhost:8000/api/flux?shower=PER&start=2012-08-01&stop=2012-08-02
    """
    try:
        shower = request.args.get('shower')
        start = time.Time(request.args.get('start'), scale='utc')
        stop = time.Time(request.args.get('stop'), scale='utc')
        year = request.args.get('year', default='', type=str)
        avg = request.args.get('avg', default='false', type=str)
        min_interval = request.args.get('min_interval', default=1, type=float)
        max_interval = request.args.get('max_interval', default=24, type=float)
        min_meteors = request.args.get('min_meteors', default=20, type=int)
        min_eca = request.args.get('min_eca', default=20000., type=float)
        min_alt = request.args.get('min_alt', default=10, type=float)
        gamma = request.args.get('gamma', default=1.5, type=float)
        popindex = request.args.get('popindex', default=2.0, type=float)
        
        years = year.split(',')
        if avg == 'false' and len(years) == 1:
            myprofile = profile.VideoProfile(MYDB, shower, start, stop,
                                           min_interval=min_interval,
                                           max_interval=max_interval,
                                           min_meteors=min_meteors,
                                           min_eca=min_eca,
                                           min_alt=min_alt,
                                           gamma=gamma,
                                           popindex=popindex)
            reponse = myprofile.get_response()
        elif avg == 'false' and len(years) > 1:
            sollon_start = util.sollon(start.datetime)
            sollon_stop = util.sollon(stop.datetime)
            profiles = []
            for myyear in years:
                profiles.append(profile.AvgVideoProfile(MYDB, 
                                           shower, [myyear],
                                           sollon_start, sollon_stop,
                                           min_interval=min_interval,
                                           max_interval=max_interval,
                                           min_meteors=min_meteors,
                                           min_eca=min_eca,
                                           min_alt=min_alt,
                                           gamma=gamma,
                                           popindex=popindex))
            mygraph = graph.SolVideoGraph(profiles)
            mygraph.plot()
            reponse = {}
            reponse['status'] = 'OK'
            reponse['graph'] = mygraph.save()
            reponse['flux'] = []
        elif avg == 'true':
            sollon_start = util.sollon(start.datetime)
            sollon_stop = util.sollon(stop.datetime)
            myprofile = profile.AvgVideoProfile(MYDB, 
                                           shower, years,
                                           sollon_start, sollon_stop,
                                           min_interval=min_interval,
                                           max_interval=max_interval,
                                           min_meteors=min_meteors,
                                           min_eca=min_eca,
                                           min_alt=min_alt,
                                           gamma=gamma,
                                           popindex=popindex)
            reponse = myprofile.get_response()
        else:
            raise ValueError('Inconsistent parameters')

        return json.jsonify(reponse)
    except ValueError, e:
        reponse = {'status':'ERROR',
                   'msg':'Invalid parameters.',
                   'debug':str(e)}
        return json.jsonify(reponse)

