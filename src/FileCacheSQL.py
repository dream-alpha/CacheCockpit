#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2022 by dream-alpha
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


import sqlite3 as sqlite
from Debug import logger
from FileCacheUtils import SQL_DB_NAME, FILE_IDX_CUTS


class FileCacheSQL():

	RECORDING_COLUMNS = [
		"directory TEXT", "file_type INTEGER", "path TEXT", "file_name TEXT", "file_ext TEXT", "name TEXT",
		"event_start_time INTEGER", "recording_start_time INTEGER", "recording_stop_time INTEGER", "length INTEGER",
		"description TEXT", "extended_description TEXT", "service_reference TEXT", "size INTEGER", "cuts BLOB", "tags TEXT"
	]

	def __init__(self):
		logger.info("...")
		self.sql_conn = sqlite.connect(SQL_DB_NAME)
		self.sqlCreateTable()

	def sqlCreateTable(self):
		columns = ", ".join(column for column in self.RECORDING_COLUMNS)
		self.sql_conn.execute("""CREATE TABLE IF NOT EXISTS recordings ({})""".format(columns))
		self.sql_conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_path ON recordings (path)""")
		self.sql_conn.text_factory = str
		self.cursor = self.sql_conn.cursor()

	def sqlClearTable(self):
		self.cursor.execute("DELETE FROM recordings")
		self.sql_conn.commit()

	def sqlSelect(self, where, args=None):
		sql = """SELECT * FROM recordings WHERE %s""" % where
		logger.debug("sql: %s, args: %s", sql, args)
		self.cursor.execute(sql, args)
		file_list = self.cursor.fetchall()
		self.sql_conn.commit()
		return file_list

	def sqlDelete(self, where, args=None):
		sql = """DELETE FROM recordings WHERE %s""" % where
		logger.debug("sql: %s, arguments: %s", sql, args)
		self.cursor.execute(sql, args)
		self.sql_conn.commit()

	def sqlInsert(self, afile):
		afile = list(afile)
		afile[FILE_IDX_CUTS] = sqlite.Binary(afile[FILE_IDX_CUTS])
		binds = ",".join("?" * len(afile))
		self.cursor.execute("""REPLACE INTO recordings VALUES ({})""".format(binds), afile)
		self.sql_conn.commit()

	def sqlClose(self):
		self.sql_conn.commit()
		self.sql_conn.close()
