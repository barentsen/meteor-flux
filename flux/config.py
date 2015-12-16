#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Constants used in the IPHAS Data Release modules."""
import os

PACKAGEDIR = os.path.dirname(os.path.abspath(__file__))

HOSTNAME = os.uname()[1]
if HOSTNAME == 'gvm':
    DEBUG = True
    DBINFO = 'host=flux.geert.io dbname=fluxdb user=postgres'
    #DBINFO = 'dbname=fluxdb user=postgres'
    TMPDIR = '/tmp'
    TMPDIR_WWW = '/tmp'
elif HOSTNAME == 'flux':  # testing machine
    DEBUG = False
    DBINFO = 'dbname=fluxdb user=postgres'
    TMPDIR = '/mnt/fluxtmp'
    TMPDIR_WWW = '/tmp'
elif HOSTNAME == 'hal' or HOSTNAME == 'imo.geert.io':
    DEBUG = True
    DBINFO = 'host=/var/run/postgresql dbname=fluxdb user=postgres'
    TMPDIR = '/var/www/tmp'
    TMPDIR_WWW = '/tmp'
else:
    DEBUG = False
    DBINFO = 'host=/var/run/postgresql dbname=fluxdb user=postgres'
    TMPDIR = '/tmp'
    TMPDIR_WWW = '/tmp'


# Database to use for unit tests
DBINFO_TESTING = 'host=/var/run/postgresql dbname=testdb user=postgres'
DPI = 80  # Default DPI of graphs
MARKERS = ['s', '^', 'o', 's', '^', 'o', 's', '^', 'o', 's', '^', 'o']
