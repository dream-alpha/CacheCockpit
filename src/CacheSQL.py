#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2025 by dream-alpha
#
# In case of reuse of this source code please do not remove this copyright.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# For more information on the GNU General Public License see:
# <http://www.gnu.org/licenses/>.


import os
import sqlite3 as sqlite
from Components.config import config
from .Debug import logger
from .FileManagerUtils import SQL_DB_MVC, SQL_DB_MDC


class CacheSQL():

    DATABASE = {
        "MVC": SQL_DB_MVC,
        "MDC": SQL_DB_MDC
    }

    TABLE_COLUMNS = {
        "MVC": {
            "TABLE1_COLUMNS": [
                "file_type INTEGER", "bookmark TEXT", "path TEXT", "rel_path TEXT", "directory TEXT", "rel_dir TEXT", "file_name TEXT", "file_ext TEXT", "name TEXT",
                "event_start_time INTEGER", "recording_start_time INTEGER", "recording_stop_time INTEGER", "length INTEGER",
                "description TEXT", "extended_description TEXT", "service_reference TEXT", "size INTEGER", "cuts TEXT",
                "sort TEXT", "host_name TEXT"
            ],
            "TABLE2_COLUMNS": [
                "path TEXT", "cover BLOB"
            ]
        },
        "MDC": {
            "TABLE1_COLUMNS": [
                "file_type INTEGER", "bookmark TEXT", "path TEXT", "rel_path TEXT", "directory TEXT", "rel_dir TEXT", "file_name TEXT", "file_ext TEXT", "name TEXT",
                "date INTEGER", "media INTEGER", "meta TEXT"
            ],
            "TABLE2_COLUMNS": [
                "path TEXT", "thumbnail BLOB"
            ]
        }
    }

    def __init__(self):
        logger.info("...")
        self.initDatabase()

    def initDatabase(self):
        database_directory = os.path.join(config.plugins.mediacockpit.database_directory.value) if self.plugin == "MDC" else os.path.join(
            config.plugins.moviecockpit.database_directory.value)
        self.sql_conn = sqlite.connect(os.path.join(
            database_directory, self.DATABASE[self.plugin]))
        self.sqlCreateTables()
        self.setCaseSensitiveLike()

    def sqlCreateTables(self):
        columns = ", ".join(
            column for column in self.TABLE_COLUMNS[self.plugin]["TABLE1_COLUMNS"])
        self.sql_conn.execute(
            """CREATE TABLE IF NOT EXISTS table1 ({})""".format(columns))
        self.sql_conn.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_table1 ON table1 (path)""")
        columns = ", ".join(
            column for column in self.TABLE_COLUMNS[self.plugin]["TABLE2_COLUMNS"])
        self.sql_conn.execute(
            """CREATE TABLE IF NOT EXISTS table2 ({})""".format(columns))
        self.sql_conn.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_table2 ON table2 (path)""")
        self.sql_conn.text_factory = str
        self.cursor = self.sql_conn.cursor()

    def sqlClearTable(self, table):
        sql = """DELETE FROM %s""" % table
        self.cursor.execute(sql)
        self.sql_conn.commit()

    def sqlClearDatabase(self):
        self.cursor.execute("PRAGMA writable_schema = 1;")
        self.cursor.execute(
            "DELETE FROM sqlite_master WHERE type IN ('table', 'index', 'trigger');")
        self.cursor.execute("PRAGMA writable_schema = 0;")
        self.cursor.execute("VACUUM;")
        self.sql_conn.commit()
        self.initDatabase()

    def setCaseSensitiveLike(self):
        self.cursor.execute("PRAGMA case_sensitive_like = true")
        self.sql_conn.commit()

    def sqlInitFile(self):
        afile = []
        for column in self.TABLE_COLUMNS[self.plugin]["TABLE1_COLUMNS"]:
            atype = column.split(" ", 1)[1]
            if atype == "TEXT":
                afile.append("")
            elif atype == "INTEGER":
                afile.append(0)
        # logger.debug("afile: %s", afile)
        return afile

    def sqlSelect(self, table, where, args):
        logger.debug("table: %s, where: %s, args: %s", table, where, args)
        if where:
            sql = """SELECT * FROM %s WHERE %s""" % (table, where)
        else:
            sql = """SELECT * FROM %s""" % table
        logger.debug("sql: %s, args: %s", sql, args)
        self.cursor.execute(sql, args)
        file_list = self.cursor.fetchall()
        self.sql_conn.commit()
        return file_list

    def sqlSelectRaw(self, sql, args):
        logger.debug("sql: %s, args: %s", sql, args)
        self.cursor.execute(sql, args)
        file_list = self.cursor.fetchall()
        self.sql_conn.commit()
        return file_list

    def sqlSelectDistinct(self, table, cols, where, args):
        sql = """SELECT DISTINCT %s FROM %s WHERE %s""" % (cols, table, where)
        logger.debug("sql: %s, args: %s", sql, args)
        self.cursor.execute(sql, args)
        file_list = self.cursor.fetchall()
        self.sql_conn.commit()
        return file_list

    def sqlDelete(self, table, where, args=None):
        sql = """DELETE FROM %s WHERE %s""" % (table, where)
        logger.debug("sql: %s, arguments: %s", sql, args)
        self.cursor.execute(sql, args)
        self.sql_conn.commit()

    def sqlInsert(self, table, afile):
        if table == "table1":
            binds = ",".join(
                "?" * len(self.TABLE_COLUMNS[self.plugin]["TABLE1_COLUMNS"]))
        else:
            binds = ",".join(
                "?" * len(self.TABLE_COLUMNS[self.plugin]["TABLE2_COLUMNS"]))
        sql = ("""REPLACE INTO %s VALUES ({})""" % table).format(binds)
        self.cursor.execute(sql, afile)
        self.sql_conn.commit()

    def sqlClose(self):
        if self.sql_conn:
            self.sql_conn.commit()
            self.sql_conn.close()
