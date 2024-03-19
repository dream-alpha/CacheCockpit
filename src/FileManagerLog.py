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


import os
import json
import six
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from .Debug import logger
from .FileUtils import readFile, writeFile
from .FileManagerUtils import FILE_TYPE_DELETED
from .FileManagerUtils import FILE_IDX_BOOKMARK, FILE_IDX_PATH, FILE_IDX_DIR, FILE_IDX_FILENAME, FILE_IDX_EXT,\
	FILE_IDX_RELPATH, FILE_IDX_TYPE, FILE_IDX_NAME, FILE_IDX_EVENT_START_TIME, FILE_IDX_RECORDING_START_TIME,\
	FILE_IDX_RELDIR, FILE_IDX_RECORDING_STOP_TIME, FILE_IDX_LENGTH, FILE_IDX_DESCRIPTION,\
	FILE_IDX_EXTENDED_DESCRIPTION, FILE_IDX_SERVICE_REFERENCE, FILE_IDX_SIZE, FILE_IDX_CUTS,\
	FILE_IDX_SORT, FILE_IDX_HOSTNAME
from .FileManagerCacheSQL import FileManagerCacheSQL


LOG_FILE_NAME = "/etc/enigma2/moviecockpit_log.json"


class FileManagerLog(FileManagerCacheSQL):

	def __init__(self, bookmarks):
		FileManagerCacheSQL.__init__(self)
		self.bookmarks = bookmarks
		if not os.path.isfile(LOG_FILE_NAME):
			json_data = []
			self.writeLogFile(json_data)

	def writeLogFile(self, json_data):
		data = json.dumps(json_data, indent=4)
		writeFile(LOG_FILE_NAME, data)

	def readLogFile(self):
		data = readFile(LOG_FILE_NAME)
		json_data = json.loads(data)
		return json_data

	def deleteLogEntry(self, path, json_data=""):
		logger.info("path: %s", path)
		if not json_data:
			json_data = self.readLogFile()
		file_name = os.path.basename(path)
		for afile in json_data:
			# logger.debug("file_name: %s, afile[FILE_IDX_RELPATH]: %s", file_name, afile[FILE_IDX_RELPATH])
			if afile[FILE_IDX_FILENAME] + afile[FILE_IDX_EXT] == file_name:
				json_data.remove(afile)
				break
		self.writeLogFile(json_data)

	def addLogEntry(self, file_list, json_data=""):
		logger.info("...")
		if not json_data:
			json_data = self.readLogFile()

		for afile in file_list:
			path = afile[FILE_IDX_PATH].replace("/trashcan", "")
			bookmark = MountCockpit.getInstance().getBookmark("MVC", path)
			path = os.path.normpath(os.path.join(bookmark, os.path.basename(path)))
			afile = list(afile)
			afile[FILE_IDX_CUTS] = ""
			afile[FILE_IDX_BOOKMARK] = bookmark
			afile[FILE_IDX_DIR] = bookmark
			afile[FILE_IDX_RELDIR] = "/"
			afile[FILE_IDX_PATH] = path
			afile[FILE_IDX_RELPATH] = os.path.basename(path)
			afile[FILE_IDX_TYPE] = FILE_TYPE_DELETED
			json_data.append(afile)
		self.writeLogFile(json_data)

	def convertLogLayout(self, afile):
		logger.info("...")
		bfile = self.sqlInitFile()
		bfile[FILE_IDX_TYPE] = afile[1]
		bfile[FILE_IDX_BOOKMARK] = MountCockpit.getInstance().getBookmark("MVC", afile[2])
		bfile[FILE_IDX_PATH] = afile[2]
		bfile[FILE_IDX_RELPATH] = os.path.abspath(os.path.relpath(afile[2], bfile[FILE_IDX_BOOKMARK]))
		bfile[FILE_IDX_DIR] = afile[0]
		bfile[FILE_IDX_RELDIR] = os.path.abspath(os.path.relpath(afile[0], bfile[FILE_IDX_BOOKMARK]))
		bfile[FILE_IDX_FILENAME] = afile[3]
		bfile[FILE_IDX_EXT] = afile[4]
		bfile[FILE_IDX_NAME] = afile[5]
		bfile[FILE_IDX_EVENT_START_TIME] = afile[6]
		bfile[FILE_IDX_RECORDING_START_TIME] = afile[7]
		bfile[FILE_IDX_RECORDING_STOP_TIME] = afile[8]
		bfile[FILE_IDX_LENGTH] = afile[9]
		bfile[FILE_IDX_DESCRIPTION] = afile[10]
		bfile[FILE_IDX_EXTENDED_DESCRIPTION] = afile[11]
		bfile[FILE_IDX_SERVICE_REFERENCE] = afile[12]
		bfile[FILE_IDX_SIZE] = afile[13]
		bfile[FILE_IDX_CUTS] = afile[14]
		bfile[FILE_IDX_SORT] = afile[15]
		if len(afile) > 16:
			bfile[FILE_IDX_HOSTNAME] = afile[16]
		return bfile

	def getLogFileList(self, adir):
		logger.info("dir: %s", adir)
		save_log_list = False
		new_json_data = []
		data = readFile(LOG_FILE_NAME)
		json_data = json.loads(data)
		file_list = []
		for json_file in json_data:
			# logger.info("json_file: %s", json_file)
			afile = []
			for aitem in json_file:
				if isinstance(aitem, six.text_type):  # pylint: disable=E0602
					aitem = str(aitem)
				afile.append(aitem)
			logger.info("afile: %s", afile)
			if len(afile) != len(self.RECORDING_COLUMNS):
				afile = self.convertLogLayout(afile)
				save_log_list = True

			path = afile[FILE_IDX_PATH]
			bookmark = MountCockpit.getInstance().getBookmark("MVC", path)
			path = os.path.normpath(os.path.join(bookmark, os.path.basename(path)))
			afile[FILE_IDX_BOOKMARK] = bookmark
			afile[FILE_IDX_DIR] = bookmark
			afile[FILE_IDX_RELDIR] = "/"
			afile[FILE_IDX_PATH] = path
			afile[FILE_IDX_RELPATH] = os.path.basename(path)
			new_json_data.append(afile)

			if adir in self.bookmarks:
				file_list.append(tuple(afile))
		if save_log_list:
			self.writeLogFile(new_json_data)
		return file_list
