meteor-flux
===========
Meteor-flux is a a Python package intended to create graphs
of meteor flux observations stored in a PostgreSQL database.

Demo
----
To run the app locally in debug mode, execute:

    python scripts/service.py

To run the app in production, Apache must be configured 
to serve `fluxapp.wsgi` through mod_wsgi.

Authors
-------
Created by Geert Barentsen with help from Sirko Molau.


License
-------
Released under MIT License, full details in `LICENSE` file.


Dependencies
------------
* numpy
* matplotlib
* astropy
* psycopg2
* flask
