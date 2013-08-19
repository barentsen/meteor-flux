#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Constants used in the IPHAS Data Release modules."""
import os

PACKAGEDIR = os.path.dirname(os.path.abspath(__file__))

HOSTNAME = os.uname()[1]
if HOSTNAME == 'gvm':  # testing machine
    DEBUG = True
    TMPDIR = '/home/gb/dev/meteor-flux/tmp'
    TMPDIR_WWW = '/meteor-flux/tmp'
    DBINFO = 'dbname=fluxdb user=postgres'
else:
    DEBUG = False
    DBINFO = 'host=flux.geert.io dbname=fluxdb user=postgres'
    TMPDIR = '/tmp'
    TMPDIR_WWW = '/tmp'

DPI = 80  # Default DPI of graphs
