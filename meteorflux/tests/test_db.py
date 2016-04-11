#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests database functionality."""
import os
import inspect
from contextlib import contextmanager

from .. import db
from .. import metrec
from .. import config

PATH = os.path.dirname(os.path.realpath(__file__))  # current dir

@contextmanager
def tempdb():
    """Ensures a clean flux table is setup and dropped."""
    mydb = db.FluxDB(config.DBINFO_TESTING)
    mydb.setup()
    yield mydb
    mydb.drop()

def test_setup():
    mydb = db.FluxDB(config.DBINFO_TESTING)
    mydb.create_tables()
    mydb.create_indexes()
    mydb.drop()

def test_metrec_ingest_v10():
    """Ingests a MetRec ZIP file containing flux data (v1.0)."""
    with tempdb() as mydb:
        zipfile = os.path.join(PATH, 'data', '20130722_ORION1.zip')
        metrec.ingest_zip(zipfile, mydb)
        # The ZIP file contains 2459 flux records
        count = mydb.query('SELECT COUNT(*) FROM flux')[0][0]
        assert(count == 2459)

def test_metrec_ingest_v11():
    """Ingests a MetRec ZIP file containing flux data (v1.1)."""
    with tempdb() as mydb:
        zipfile = os.path.join(PATH, 'data', '20140419_REMO2.zip')
        metrec.ingest_zip(zipfile, mydb)
        # The ZIP file contains 2459 flux records
        #count = mydb.query('SELECT COUNT(*) FROM flux')[0][0]
        #assert(count == 2459)