#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tests database functionality."""
import os
import inspect
from contextlib import contextmanager

from .. import db
from .. import metrec

PATH = os.path.dirname(os.path.realpath(__file__))
TESTDB = "dbname=test user=postgres"

@contextmanager
def tempdb():
    """Ensures a clean flux table is setup and dropped."""
    mydb = db.FluxDB(TESTDB)
    mydb.setup()
    yield mydb
    mydb.drop()


def test_setup():
    mydb = db.FluxDB(TESTDB)
    mydb.create_tables()
    mydb.create_indexes()
    mydb.drop()


def test_metrec_ingest():
    """Ingests a MetRec ZIP file containing flux data."""
    with tempdb() as mydb:
        zipfile = os.path.join(PATH, 'data', '20130722_ORION1.zip')
        metrec.ingest_zip(zipfile, mydb)
        # The ZIP file contains 2459 flux records
        count = mydb.query('SELECT COUNT(*) FROM flux')[0][0]
        assert(count == 2459)

