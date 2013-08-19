#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Starts the Flask app in debug mode.

Do not use in production.
"""
from flux.app import fluxapp

if __name__ == "__main__":
    fluxapp.debug = True
    fluxapp.run(port=8042, host='0.0.0.0')
