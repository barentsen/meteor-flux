"""Configuration constants."""
import os

PACKAGEDIR = os.path.dirname(os.path.abspath(__file__))

HOSTNAME = os.uname()[1]
if HOSTNAME == 'ec.geert.io' or HOSTNAME == 'imo.geert.io' or HOSTNAME == 'meteorflux.io':
    DEBUG = True
    DBINFO = 'host=/var/run/postgresql dbname=flux_kca user=postgres'
    TMPDIR = '/var/www/tmp'
    TMPDIR_WWW = '/tmp'
else:
    DEBUG = True
    DBINFO = 'host=/var/run/postgresql dbname=fluxdb user=postgres'
    TMPDIR = '/tmp'
    TMPDIR_WWW = '/tmp'


# Database to use for unit tests
DBINFO_TESTING = 'host=/var/run/postgresql dbname=testdb user=postgres'
DPI = 80  # Default DPI of graphs
MARKERS = ['s', '^', 'o', 's', '^', 'o', 's', '^', 'o', 's', '^', 'o']

