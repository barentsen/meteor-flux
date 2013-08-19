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

import config


class FluxDB(object):

    def __init__(self,
                 dbinfo=config.DBINFO,
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
        if json['dist'] is None:
            json['dist'] = ''
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
        log.info('Creating index on dataset_id')
        self.cur.execute("""CREATE INDEX {0}_dataset_idx ON {0}
                            USING btree (dataset_id);""".format(
                                                         self.fluxtable))
        log.info('Creating index on (time,shower)')
        self.cur.execute("""CREATE INDEX {0}_time_shower_idx ON {0}
                            USING btree (time, shower);""".format(
                                                           self.fluxtable))
        log.info('Creating index on (sollong, shower)')
        self.cur.execute("""CREATE INDEX {0}_sollong_shower_idx ON {0}
                            USING btree (sollong, shower);""".format(
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

