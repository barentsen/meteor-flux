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
from flask import Flask, request
from flux import db, graph

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

    result = graph.VideoFluxProfile(MYDB, shower, start, stop,
                                   min_interval=min_interval,
                                   max_interval=max_interval,
                                   min_meteors=min_meteors,
                                   min_eca=min_eca,
                                   min_alt=min_alt,
                                   gamma=gamma,
                                   popindex=popindex)
    return result.get_json()



if __name__ == "__main__":
    port = 8000
    # Set up the development server on port 8000.
    app.debug = True
    app.run(port=port)
