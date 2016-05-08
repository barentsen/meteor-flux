"""Flask app to graph video meteor fluxes.

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
from astropy import time

from . import db, profile, graph, util, config

fluxapp = Flask('meteorflux', static_url_path='')

@fluxapp.route('/')
def root():
    return fluxapp.send_static_file('index.html')

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
        ymax = request.args.get('ymax', default=None, type=float)
        
        mydb = db.FluxDB()

        years = year.split(',')
        if avg == 'false' and len(years) == 1:
            myprofile = profile.VideoProfile(mydb, shower, start, stop,
                                           min_interval=min_interval,
                                           max_interval=max_interval,
                                           min_meteors=min_meteors,
                                           min_eca=min_eca,
                                           min_alt=min_alt,
                                           gamma=gamma,
                                           popindex=popindex,
                                           ymax=ymax)
            reponse = myprofile.get_response()
        elif avg == 'false' and len(years) > 1:
            sollon_start = util.sollon(start.datetime)
            sollon_stop = util.sollon(stop.datetime)
            profiles = []
            for i, myyear in enumerate(years):
                profiles.append(profile.AvgVideoProfile(mydb, 
                                           shower, [myyear],
                                           sollon_start, sollon_stop,
                                           min_interval=min_interval,
                                           max_interval=max_interval,
                                           min_meteors=min_meteors,
                                           min_eca=min_eca,
                                           min_alt=min_alt,
                                           gamma=gamma,
                                           popindex=popindex,
                                           ymax=ymax,
                                           marker=config.MARKERS[i]))
            mygraph = graph.SolVideoGraph(profiles, ymax=ymax)
            mygraph.plot()
            reponse = {}
            reponse['status'] = 'OK'
            reponse['graph'] = mygraph.save()
            reponse['flux'] = []
        elif avg == 'true':
            sollon_start = util.sollon(start.datetime)
            sollon_stop = util.sollon(stop.datetime)
            myprofile = profile.AvgVideoProfile(mydb, 
                                           shower, years,
                                           sollon_start, sollon_stop,
                                           min_interval=min_interval,
                                           max_interval=max_interval,
                                           min_meteors=min_meteors,
                                           min_eca=min_eca,
                                           min_alt=min_alt,
                                           gamma=gamma,
                                           popindex=popindex,
                                           ymax=ymax)
            reponse = myprofile.get_response()
        else:
            raise ValueError('Inconsistent parameters')

        return json.jsonify(reponse)
    except ValueError as e:
        reponse = {'status':'ERROR',
                   'msg':'Invalid parameters.',
                   'debug':str(e)}
        return json.jsonify(reponse)

