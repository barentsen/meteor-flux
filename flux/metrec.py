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

import db

##########
# CLASSES
##########

class MetRecData(object):
    """Class representing a ZIP file with flux data generated by MetRec.
    """

    def __init__(self, filename):
        """
        Arguments
        ---------
        filename : string
            Path to the filename of a ZIP-file containing MetRec flux data.

        Exceptions
        ----------
        BadZipfile: if zip_filename not a valid ZIP file
        """
        self.filename = filename
        self.zipfile = zipfile.ZipFile(self.filename)
        self.dataset_id = self.filename.split("/")[-1].split(".")[0]
        self.station = self.dataset_id.split("_")[1].upper()

    def _parse_flx(self, filename):
        """Parse a MetRec .FLX file

        Arguments
        ---------
        filename : filename of the .FLX file within the ZIP file.

        Returns
        -------
        A list of dictionaries, one per flux measurement, of the form
        {'dataset_id': ...,
         'format': ...,
         'station': ...,
         'shower': ...,
         'time': ...,
         }.
        """
        out = []

        flx_data = self.zipfile.read(filename)

        # Check all lines for header data
        for l in flx_data.splitlines():
            fields = l.split()
            if len(fields) > 0:
                if fields[0] == "Format":
                    fileformat = "_".join(fields[1:])
                elif fields[0] == "Date":
                    year = int(fields[1][0:4])
                    month = int(fields[1][4:6])
                    day = int(fields[1][6:8])
                elif fields[0] == "IMO" and fields[1] == "Code":
                    showercode = fields[2]

        # We need to deal with the fact that two extra columns
        # have been added in file format FLX v1.1
        if fileformat == 'MetRec_FLX_1.0':
            eca_idx, met_idx, mag_idx = 9, 10, 11
        else:
            eca_idx, met_idx, mag_idx = 11, 12, 13

        # Check all lines for flux data
        starthour = None
        for l in flx_data.splitlines():
            fields = l.split()
            if len(fields) > 5:
                time = fields[0].split(":")
                if len(time) == 2:
                    hour = int(time[0])
                    if starthour == None:
                        starthour = hour
                    minute = int(time[1])
                    mytime = datetime.datetime(year, month, day, hour, minute, 0, 0)
                    if hour < starthour:
                        mytime = mytime + datetime.timedelta(1)
                    # Missing values are indicated by dashes
                    is_valid = True
                    for index in [1, 2, 3, 4, 6, 7, 8, eca_idx, met_idx]:
                        if fields[index] == "-" or fields[index].find("--") > -1:
                            # fields[index] = None
                            is_valid = False
                            continue

                    # We must be tolerant towards missing "distance" value due to SPO
                    if fields[5] == "-":
                        dist = None
                    else:
                        dist = fields[5]

                    if is_valid:
                        row = { "dataset_id": self.dataset_id, 
                                "format": fileformat,
                                "station": self.station, 
                                "shower": showercode, 
                                "time": mytime,
                                "sollong": float(fields[1]), 
                                "teff": float(fields[2]), 
                                "lmstar": float(fields[3]), 
                                "alt": float(fields[4]),
                                "dist": dist, 
                                "vel": float(fields[6]), 
                                "mlalt": float(fields[7]), 
                                "lmmet": float(fields[8]), 
                                "eca": float(fields[eca_idx]), 
                                "met": int(fields[met_idx]),
                                "mag": [float(m) for m in fields[mag_idx:]],
                                "added": str(datetime.datetime.now()) }
                        out.append(row)
        return out 

    def get_json(self):
        """Returns the flux data in the MetRec file as a list of dicts.

        Returns
        -------
        A list of dictionaries, one per flux measurements, 
        which can be handed over to pymongo.insert.
        """
        data = []
        for filename in self.zipfile.namelist():
            if filename.upper().endswith(".FLX"):
                log.debug("Reading %s/%s" % (self.dataset_id, filename))
                data += self._parse_flx(filename)
        return data


###########
# FUNCTIONS
###########

def ingest_zip(path, mydb, remove_old=True):
    """Adds a single metrec flux zip file to the database.

    Parameters
    ----------
    path : str
        Location of the data.

    mydb : FluxDB object
        Database in which to ingest.

    remove_old : bool
        If true, search and delete any previous version of a file with
        the same filename (i.e. dataset_id). This slows things down!

    Returns
    -------
    MetRecData object that was ingested.
    """
    log.info("Ingesting %s" % path)
    myzip = MetRecData(path)
    # Make sure any previous version of this dataset is removed
    if remove_old:
        mydb.remove_dataset(myzip.dataset_id)
    mydb.ingest_json(myzip.get_json())
    return myzip

def ingest_dir(path, mydb, remove_old=True):
    """Ingest a directory of MetRec zipped flux files.

    Parameters are identical to ingest_zip().
    """
    for filename in os.listdir(path):
        full_path = os.path.join(path, filename)
        if not os.path.isdir(full_path):
            try:
                myzip = ingest_zip(full_path, mydb, remove_old)
            except zipfile.BadZipfile:
                log.warning("%s is not a valid ZIP file." % filename)
            except Exception as e:
                log.error('Unexpected error {0}'.format(e))    
