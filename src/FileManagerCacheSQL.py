#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2024 by dream-alpha
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
from .Debug import logger
from .FileManagerUtils import SQL_DB_NAME


class FileManagerCacheSQL():

	RECORDING_COLUMNS = [
		"file_type INTEGER", "bookmark TEXT", "path TEXT", "rel_path TEXT", "directory TEXT", "rel_dir TEXT", "file_name TEXT", "file_ext TEXT", "name TEXT",
		"event_start_time INTEGER", "recording_start_time INTEGER", "recording_stop_time INTEGER", "length INTEGER",
		"description TEXT", "extended_description TEXT", "service_reference TEXT", "size INTEGER", "cuts TEXT",
		"sort TEXT", "host_name TEXT"
	]

	COVER_COLUMNS = [
		"path TEXT", "cover BLOB"
	]

	def __init__(self):
		logger.info("...")
		self.sql_conn = sqlite.connect(SQL_DB_NAME)
		self.sqlCreateTable()
		self.setCaseSensitiveLike()

	def sqlCreateTable(self):
		columns = ", ".join(column for column in self.RECORDING_COLUMNS)
		self.sql_conn.execute("""CREATE TABLE IF NOT EXISTS recordings ({})""".format(columns))
		self.sql_conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_recordings ON recordings (path)""")
		columns = ", ".join(column for column in self.COVER_COLUMNS)
		self.sql_conn.execute("""CREATE TABLE IF NOT EXISTS covers ({})""".format(columns))
		self.sql_conn.execute("""CREATE UNIQUE INDEX IF NOT EXISTS idx_covers ON covers (path)""")
		self.sql_conn.text_factory = str
		self.cursor = self.sql_conn.cursor()

	def sqlClearTable(self, table):
		sql = """DELETE FROM %s""" % table
		self.cursor.execute(sql)
		self.sql_conn.commit()

	def setCaseSensitiveLike(self):
		self.cursor.execute("PRAGMA case_sensitive_like = true")
		self.sql_conn.commit()

	def sqlInitFile(self):
		afile = []
		for column in self.RECORDING_COLUMNS:
			atype = column.split(" ", 1)[1]
			if atype == "TEXT":
				afile.append("")
			elif atype == "INTEGER":
				afile.append(0)
		logger.debug("afile: %s", afile)
		return afile

	def sqlSelect(self, table, where, args):
		if where:
			sql = """SELECT * FROM %s WHERE %s""" % (table, where)
		else:
			sql = """SELECT * FROM %s""" % table
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
		if table == "recordings":
			binds = ",".join("?" * len(self.RECORDING_COLUMNS))
		else:
			binds = ",".join("?" * len(self.COVER_COLUMNS))
		sql = ("""REPLACE INTO %s VALUES ({})""" % table).format(binds)
		self.cursor.execute(sql, afile)
		self.sql_conn.commit()

	def sqlClose(self):
		if self.sql_conn:
			self.sql_conn.commit()
			self.sql_conn.close()
