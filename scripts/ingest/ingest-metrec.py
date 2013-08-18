#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Parse MetRec flux data for ingestion into the database.

"""
import os
import sys
import zipfile
import datetime
from astropy import log

from flux import metrec
from flux import db

#######
# MAIN
#######

if __name__ == '__main__':

    # Check if we have an argument
    if len(sys.argv) < 2:
        raise Exception("Please supply the name of a ZIP file.")
    path = sys.argv[1]

    #log.setLevel('DEBUG')
    #with log.log_to_file('ingestion.log'):

    mydb = db.FluxDB(autocommit=False)

    if os.path.isdir(path):
        log.info("%s is a directory, will ingest all *.zip files inside." % path)
        metrec.ingest_dir(path, mydb)
    else:
        myzip = metrec.ingest_zip(path, mydb)

    mydb.commit()
