meteor-flux
===========
Meteor-flux is a a Python package intended to create graphs
of meteor flux observations stored in a PostgreSQL database.

Demo
----
To see the app in action, visit `meteorflux.io <meteorflux.io>`_.

Usage
-----
To run the app locally in debug mode, execute::

  python scripts/service.py

To run the app in production, see the `Flask` documentation for
configuring Nginx or Apache.

Authors
-------
Geert Barentsen, Sirko Molau.

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
