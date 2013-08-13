#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flux database.

"""
import os
import psycopg2
import psycopg2.extras
from StringIO import StringIO
from astropy import log


class FluxDB(object):

    def __init__(self,
                 dbinfo='dbname=fluxdb user=postgres',
                 prefix='', 
                 autocommit=True):
        """Constructor

        Parameters
        ----------
        dbname : string
            Connection settings passed on to the psycopg2 module.

        autocommit : boolean
            If true, changes will be commited on each operation.
        """
        self.conn = psycopg2.connect(dbinfo,
                                     cursor_factory=psycopg2.extras.DictCursor)
        self.cur = self.conn.cursor()
        self.prefix = prefix
        self.autocommit = autocommit

        self.fluxtable = self.prefix+'flux'

    def __del__(self):
        """Destructor"""
        self.cur.close()
        self.conn.close()


    ################
    # DATA QUERYING
    ################

    def query(self, sql, arguments=()):
        try:
            self.cur.execute(sql, arguments)
            return self.cur.fetchall()
        except psycopg2.ProgrammingError as e:
            log.error('Query failed [{0}] with error message[{1}]'.format(
                                self.cur.query, e))
            self.rollback()
            return None

    #def query_json(self, sql, arguments=(,)):
    #    result = self.query(sql, arguments)
    #    for key in result[0].keys():
    #        "{0}: {}"

    def bin_adaptive(self, shower, start, stop,
                     min_interval=1, max_interval=24,
                     min_meteors=20, min_eca=20, 
                     min_alt=10, min_eca_station=0.5,
                     gamma=1.5, popindex=2.0):
        """Returns a binned flux profile table.

        Parameters
        ----------
        shower : string
            IMO shower code

        start : string
            ISO timestamp

        stop : string
            ISO timestamp

        min_meteors : int
            Minimum number of meteors in each bin.

        min_eca : float [10^3 km^2 h]
            Minimum ECA in each bin.

        min_interval : float [hours]

        max_interval : float [hours]

        min_alt : float [degrees]
            Minimum radiant altitude for a flux record to be included.

        min_eca_station : float [degrees]
            Minimum ECA for a flux record to be included.

        gamma : float
            Zenith correction exponent.

        popindex : float
            Population index.

        Returns
        -------
        Result of the query.
        """
        return self.query("""SELECT * FROM
                             bin_adaptive(%s, %s::timestamp, %s::timestamp,
                                          %s, %s,
                                          '%s hours'::interval,
                                          '%s hours'::interval,
                                          %s, %s, %s, %s)
                          """, (shower, start, stop,
                                min_meteors, min_eca,
                                min_interval, max_interval,
                                min_alt, min_eca_station,
                                gamma, popindex, ))


    ################
    # DATA INGESTION
    ################

    def commit(self):
        """Commits changes."""
        self.conn.commit()

    def rollback(self):
        """Undo changes or reset error."""
        self.conn.rollback()

    def ingest_json(self, json):
        """
        Parameters
        ----------
        json : a list of dictionaries
        """
        lines = [self._json2csv(row) for row in json]
        csvfile = StringIO("\n".join(lines))
        self.ingest_csv(csvfile)

    def ingest_csv(self, csvfile):
        """
        Parameters
        ----------
        csvfile : a file-like object which supports read() and readline()
        """
        self.cur.copy_expert('COPY flux FROM STDIN WITH CSV', csvfile)
        if self.autocommit:
            self.commit()

    def _json2csv(self, json):
        """Converts a Python dictionary to a CSV line for database ingestion

        Parameters
        ----------
        json : Python dictionary object
        """
        # The magnitude array requires special formatting: "{1,2,3}"
        magnitudes = [str(m) for m in json['mag']]
        json['mag'] = '"{' + (','.join(magnitudes)) + '}"'
        csv = "{dataset_id},{format},{station},{shower},{time},{sollong}," + \
              "{teff},{lmstar},{alt},{dist},{vel},{mlalt},{lmmet},{eca},{met}," + \
              "{mag},{added}"
        return csv.format(**json)

    def remove_dataset(self, dataset_id):
        """Removes a single dataset from the database.

        Parameters
        ----------
        dataset_id : string
            Unique identifier of the dataset, e.g. "20120723_ORION1".
        """
        self.cur.execute("DELETE FROM flux WHERE dataset_id = %s",
                         (dataset_id,))
        log.debug(self.cur.query)
        if self.autocommit:
            self.commit()


    #############################################
    # DATABASE SETUP (TABLES, INDEXES, FUNCTIONS)
    #############################################

    def setup(self):
        """Setup the database tables and indexes."""
        self.create_tables()
        self.create_indexes()
        self.create_functions()

    def drop(self):
        """Drops the tables."""
        log.info('DROP TABLE {0}'.format(self.fluxtable)) 
        self.cur.execute("""DROP TABLE {0}""".format(self.fluxtable))
        if self.autocommit:
            self.commit()  

    def create_tables(self):
        """Setup the database. Should not commonly be used.
        """
        log.info('CREATE TABLE {0}'.format(self.fluxtable))
        self.cur.execute("DROP TABLE IF EXISTS {0};".format(self.fluxtable))
        self.cur.execute("""CREATE TABLE {0} (
                                dataset_id text,
                                format text,
                                station text,
                                shower text,
                                time timestamp,
                                sollong real,
                                teff real,
                                lmstar real,
                                alt real,
                                dist real,
                                vel real,
                                mlalt real,
                                lmmet real,
                                eca real,
                                met int,
                                mag real[],
                                added timestamp
                            );""".format(self.fluxtable))
        if self.autocommit:
            self.commit()

    def create_indexes(self):
        """Creates the indexes needed.
        """
        log.info('Creating indexes on {0}'.format(self.fluxtable))
        self.cur.execute("""CREATE INDEX {0}_dataset_idx ON {0}
                            USING btree (dataset_id);""".format(
                                                         self.fluxtable))
        self.cur.execute("""CREATE INDEX {0}_time_shower_idx ON {0}
                            USING btree (time, shower);""".format(
                                                           self.fluxtable))
        if self.autocommit:
            self.commit()

    def create_functions(self):
        """Create the stored procedures.
        """
        PATH = os.path.dirname(os.path.realpath(__file__))
        filename = os.path.join(PATH, 'lib', 'functions.sql')
        with open(filename, 'r') as myfile:
            sql = "".join(myfile.readlines())
            self.cur.execute(sql)
        if self.autocommit:
            self.commit()        
