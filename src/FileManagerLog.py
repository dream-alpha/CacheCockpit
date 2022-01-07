#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2023 by dream-alpha
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
import json
import six
from .Debug import logger
from .FileUtils import readFile, writeFile
from .FileManagerUtils import FILE_TYPE_FILE, FILE_TYPE_DELETED, FILE_IDX_TYPE, FILE_IDX_DIR, FILE_IDX_PATH, FILE_IDX_CUTS


LOG_FILE_NAME = "/etc/enigma2/moviecockpit_log.json"


class FileManagerLog():

	def __init__(self, bookmarks):
		self.bookmarks = bookmarks

	def getFile(self, _table, _path):
		logger.error("should be overridden in child class")
		afile = []
		return afile

	def handleLogEntry(self, table, path):
		logger.info("table: %s, path: %s", table, path)
		data = readFile(LOG_FILE_NAME)
		json_data = json.loads(data)
		afile = self.getFile(table, path)
		if afile and afile[FILE_IDX_TYPE] == FILE_TYPE_FILE:
			self.addLogEntry(list(afile), json_data)
		else:
			self.deleteLogEntry(path, json_data)

	def deleteLogEntry(self, path, json_data):
		logger.info("path: %s, json_data: %s", path, json_data)
		for afile in json_data:
			if afile[FILE_IDX_PATH] == path:
				json_data.remove(afile)
				break
		data = json.dumps(json_data, indent=4)
		writeFile(LOG_FILE_NAME, data)

	def addLogEntry(self, afile, json_data):
		logger.info("...")
		afile[FILE_IDX_CUTS] = ""
		afile[FILE_IDX_DIR] = afile[FILE_IDX_DIR].replace("/trashcan", "")
		afile[FILE_IDX_PATH] = afile[FILE_IDX_PATH].replace("/trashcan", "")
		afile[FILE_IDX_TYPE] = FILE_TYPE_DELETED
		json_data.append(afile)
		data = json.dumps(json_data, indent=4)
		writeFile(LOG_FILE_NAME, data)

	def getLogFileList(self, dirs):
		if not dirs:
			dirs = self.bookmarks
		logger.info("dirs: %s", dirs)
		data = readFile(LOG_FILE_NAME)
		json_data = json.loads(data)
		file_list = []
		for json_file in json_data:
			logger.info("json_file: %s", json_file)
			afile = []
			for aitem in json_file:
				if isinstance(aitem, six.text_type):  # pylint: disable=E0602
					aitem = str(aitem)
				afile.append(aitem)
			logger.info("afile: %s", afile)
			if os.path.dirname(afile[FILE_IDX_PATH]) in dirs:
				file_list.append(tuple(afile))
		return file_list
