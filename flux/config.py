#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Constants used in the IPHAS Data Release modules."""
import os

PACKAGEDIR = os.path.dirname(os.path.abspath(__file__))

HOSTNAME = os.uname()[1]
if HOSTNAME == 'uhppc11.herts.ac.uk':  # testing machine
    DEBUG = False
    TMPDIR = '/tmp'
    TMPDIR_WWW = '/tmp'
if HOSTNAME == 'gvm':  # testing machine
    DEBUG = True
    TMPDIR = '/home/gb/dev/meteor-flux/tmp'
    TMPDIR_WWW = '/meteor-flux/tmp'

DPI = 80  # Default DPI of graphs
