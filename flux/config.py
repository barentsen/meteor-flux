#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Constants used in the IPHAS Data Release modules."""
import os

PACKAGEDIR = os.path.dirname(os.path.abspath(__file__))

HOSTNAME = os.uname()[1]
if HOSTNAME == 'gvm':
    DEBUG = True
    DBINFO = 'dbname=fluxdb user=postgres'
    TMPDIR = '/home/gb/dev/meteor-flux/tmp'
    TMPDIR_WWW = '/meteor-flux/tmp'
if HOSTNAME == 'flux':  # testing machine
    DEBUG = False
    DBINFO = 'dbname=fluxdb user=postgres'
    TMPDIR = '/mnt/tmp'
    TMPDIR_WWW = '/tmp'
else:
    DEBUG = False
    DBINFO = 'host=flux.geert.io dbname=fluxdb user=postgres'
    TMPDIR = '/tmp'
    TMPDIR_WWW = '/tmp'

DPI = 80  # Default DPI of graphs
