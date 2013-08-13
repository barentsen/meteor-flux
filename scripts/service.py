"""
Starts the fluxviewer back-end API.

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

Returns:
JSON objects with flux data and link to image.

"""
from flux import db
from flask import Flask, request

app = Flask(__name__)
MYDB = db.FluxDB()

@app.route("/")
def index():
    """When you request the root path, you'll get the index.html"""
    return "Hello world"

@app.route('/api/flux', methods=['GET'])
def get_flux():
    """Returns flux data.

    Example
    -------
    http://localhost:8000/api/flux?shower=PER&start=2012-08-01&stop=2012-08-02
    """
    shower = request.args.get('shower')
    start = request.args.get('start')
    stop = request.args.get('stop')
    min_interval = request.args.get('min_interval', default=1, type=float)
    max_interval = request.args.get('max_interval', default=24, type=float)
    min_meteors = request.args.get('min_meteors', default=20, type=int)
    min_eca = request.args.get('min_eca', default=20, type=float)
    min_alt = request.args.get('min_alt', default=10, type=float)
    gamma = request.args.get('gamma', default=1.5, type=float)
    popindex = request.args.get('popindex', default=2.0, type=float)

    result = MYDB.bin_adaptive(shower, start, stop,
                               min_interval=min_interval,
                               max_interval=max_interval,
                               min_meteors=min_meteors,
                               min_eca=min_eca,
                               min_alt=min_alt,
                               gamma=gamma,
                               popindex=popindex)

    if result is not None and len(result) > 0:
        keys = result[0].keys()
        json = '{"status":"OK", "flux": ['
        for i, row in enumerate(result):
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
    return '{"status":"ERROR"}'



if __name__ == "__main__":
    port = 8000
    # Set up the development server on port 8000.
    app.debug = True
    app.run(port=port)
