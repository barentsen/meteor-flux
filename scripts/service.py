"""Starts the Flask app in debug mode.

Do not ever use this script in production.
"""
from meteorflux import fluxapp

if __name__ == "__main__":
    fluxapp.debug = True
    fluxapp.run(port=8042, host='0.0.0.0', processes=3)
