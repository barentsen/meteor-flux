Meteorflux app
==============
Meteorflux is a Python-powered web service to create graphs of meteor flux observations
obtained by the MetRec software and stored in a PostgreSQL database.

Demo
----
To see the app in action, visit `http://meteorflux.io <http://meteorflux.io>`_.

Installation
------------
To install the ``meteorflux`` Python package, you will need to have a working version of Python 2 or 3.
If this requirement is met, you can clone this repository and install the package using::

  $ git clone https://github.com/barentsen/meteor-flux.git
  $ cd meteor-flux
  $ python setup.py install

You will also need to install and run a PostgreSQL server, and create a database, to store the flux data.
The connection details and name of this database need to be configured in the ``config.py`` module of the package,
after which you will have to run the above ``python setup.py install`` command again.

Once this is done, you can create the table that will hold the flux data, and create the associated
indexes, by executing::

  $ python scripts/setup-database.py

After this you can ingest MetRec data files using the ingestion scripts, e.g.::

  $ python scripts/ingest-metrec-data.py /path/to/directory/with/metrec/zip/files

Finally, you need to run the web service. To run the app locally in debug mode, you can execute::

  python scripts/service.py

Note however that running the web app in this way is insecure.
To run the app in production, see the `Flask` documentation for
configuring Nginx or Apache to expose this application.

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
