#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Starts the Flask app in debug mode.
"""
from flux import app

if __name__ == "__main__":
    port = 8042
    # Set up the development server on port 8000.
    app.debug = True
    app.run(port=port)
