#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Utility functions."""
import numpy as np
import math as m
import datetime
from datetime import timedelta
from flask import make_response, request, current_app
from functools import update_wrapper

def flux2zhr(flux, pop_index=2.0):
    """Eqn 41 from (Koschak 1990b)

    Parameters
    ----------
    flux : float [1000^-1 km^-2 h^-2]
    """    
    r = pop_index
    flux = flux / 1000.0
    zhr = (flux * 37200.0) / ( (13.1*r - 16.45) * (r - 1.3)**0.748 )
    return zhr


def jd(mydate):
    """Convert a Gregorian date/time in Universal Time to the corresponding Julian Day.
    This is the number of days since Greenwich noon of January 1, 4713 B.C.
    Algorithm from 'Astronomical Algorithms', Jean Meeus, p61.
    
    Parameters
    ----------
    mydate : Python DateTime object (UT) to convert
    
    Returns
    -------
    Decimal Julian Day (float)
    
    Examples
    --------
    >>> jd(datetime.datetime(2000, 1, 1, 12, 0, 0))
    2451545.0

    >>> jd(datetime.datetime(2000, 1, 1, 12, 0, 0, int(1E5)))
    2451545.0000011576
    """
    # Get the day expressed as a decimal number
    year = mydate.year
    month = mydate.month
    day_decimal = mydate.day + (mydate.hour / 24.0) + (mydate.minute / 1440.0) + ( (mydate.second + (mydate.microsecond/1E6)) / 86400.0)
    # In this algorithm, January and February have to be considered as "13th and 14th month"
    if (month == 1 or month == 2):
        month = month + 12
        year = year - 1 
    # Calculate A and B
    A = np.floor( year / 100.0 )
    B = 2 - A + np.floor( A / 4.0 )
    # Calculate the Julian Day
    result = np.floor(365.25 * (year + 4716)) + np.floor(30.6001 * (month + 1)) + day_decimal + B - 1524.5
    return result


def sollon(datetime):
    """Returns the solar longitude in decimal degrees.

    Calculation of the solar longitude with an accuracy of about .003 deg
    Algorithm based on Jean Meeus' "Astronomical Algorithms" and an article by C. Steyaert in WGN
    Parameter 1: timestamp
    Returns: solar longitude in decimal degrees
    
    Original version: 1995 Jan 28 Rainer Arlt, translated to plpgsql by Geert Barentsen in 2004
    """
    # Numbers from "Astronomical Algorithms" (Jean Meeus) pp 205
    a0 = [334166.0, 3489.0, 350.0, 342.0, 314.0, 268.0, 234.0, 132.0, 127.0, 120.0, 99.0, 90.0, 86.0, 78.0, 75.0, 51.0, 49.0, 36.0, 32.0, 28.0, 27.0, 24.0, 21.0, 21.0, 20.0, 16.0, 13.0, 13.0]
    b0 = [4.669257, 4.6261, 2.744, 2.829, 3.628, 4.418, 6.135, 0.742, 2.037, 1.11, 5.233, 2.045, 3.508, 1.179, 2.533, 4.58, 4.21, 2.92, 5.85, 1.90, 0.31, 0.34, 4.81, 1.87, 2.46, 0.83, 3.41, 1.08]
    c0 = [6283.07585, 12566.1517, 5753.385, 3.523, 77713.771, 7860.419, 3930.210, 11506.77, 529.691, 1577.344, 5884.927, 26.298, 398.149, 5223.694, 5507.553, 18849.23, 775.52, 0.07, 11790.63, 796.30, 10977.08, 5486.78, 2544.31, 5573.14, 6069.78, 213.30, 2942.46, 20.78]
    a1 = [20606.0, 430.0, 43.0]
    b1 = [2.67823, 2.635, 1.59]
    julian = jd(datetime)
    T = (julian - 2451545.0) / 365250.0
    result = 4.8950627 + T * (6283.0758500 - T * 0.0000099)

    # Calculate s0
    s0 = 0.0
    for n in range(len(b0)):
        angle = b0[n] + c0[n] * T
        s0 = s0 + a0[n] * np.cos(angle)

    # Calculate s1
    s1 = 0.0
    for n in range(3):
        angle = b1[n] + c0[n] * T
        s1 = s1 + a1[n] * np.cos(angle)

    # Calculate s2
    angle = 1.073 + c0[0] * T
    angle1 = 0.44 + c0[1] * T
    s2 = 872.0 * np.cos(angle) + 29 * np.cos(angle1)
    
    # Calculate s3
    angle = 5.84 + c0[0] * T
    s3 = 29.0 * np.cos(angle)
    
    # The required longitude in radians is given by:
    result = result + ( s0 + T * ( s1 + T * ( s2 + T * s3 ) ) ) * 1.0e-7
    
    # Normalize the angle
    while result > 2.0*np.pi:
        result = result - 2.0*np.pi
    while result < 0:
        result = result + 2.0*np.pi
    
    # Return the result (DEGREES!)
    return np.degrees(result)


# Flask crossdomain decorator

def crossdomain(origin=None, methods=None, headers=None,
                max_age=21600, attach_to_all=True,
                automatic_options=True):
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    if headers is not None and not isinstance(headers, str):
        headers = ', '.join(x.upper() for x in headers)
    if not isinstance(origin, str):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        def wrapped_function(*args, **kwargs):
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers

            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator