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
import time
import socket
from datetime import datetime
import six.moves.cPickle as cPickle
from Components.config import config
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from .Debug import logger
from .ParserEitFile import ParserEitFile
from .ParserMetaFile import ParserMetaFile
from .ServiceUtils import EXT_TS, ALL_VIDEO
from .FileUtils import readFile, deleteFile
from .DelayTimer import DelayTimer
from .FileManagerUtils import SQL_DB_NAME, FILE_TYPE_FILE, FILE_TYPE_DIR, FILE_TYPE_LINK
from .FileManagerUtils import FILE_IDX_BOOKMARK, FILE_IDX_PATH, FILE_IDX_DIR, FILE_IDX_FILENAME, FILE_IDX_EXT,\
	FILE_IDX_RELPATH, FILE_IDX_TYPE, FILE_IDX_NAME, FILE_IDX_EVENT_START_TIME, FILE_IDX_RECORDING_START_TIME,\
	FILE_IDX_RELDIR, FILE_IDX_RECORDING_STOP_TIME, FILE_IDX_LENGTH, FILE_IDX_DESCRIPTION,\
	FILE_IDX_EXTENDED_DESCRIPTION, FILE_IDX_SERVICE_REFERENCE, FILE_IDX_SIZE, FILE_IDX_CUTS,\
	FILE_IDX_SORT, FILE_IDX_HOSTNAME
from .FileManagerUtils import FILE_OP_LOAD, FILE_OP_DELETE, FILE_OP_MOVE, FILE_OP_COPY
from .VideoUtils import getFfprobeDuration
from .FileManagerLog import FileManagerLog
from .CutListUtils import unpackCutList
from .RecordingUtils import getRecordings


class FileManagerCache(FileManagerLog):

	def __init__(self):
		logger.info("...")
		self.database_loaded = False
		self.database_loaded_callback = None
		self.database_changed_callback = None
		self.epglang = config.plugins.moviecockpit.epglang.value
		self.bookmarks = MountCockpit.getInstance().getMountedBookmarks("MVC")
		FileManagerLog.__init__(self, self.bookmarks)
		if not os.path.exists(SQL_DB_NAME) or os.path.exists("/etc/enigma2/.cachecockpit"):
			logger.info("loading database...")
			deleteFile("/etc/enigma2/.cachecockpit")
			MountCockpit.getInstance().onInitComplete(self.loadDatabase)
		else:
			logger.info("database is already loaded.")
			self.database_loaded = True
		self.files_total = 0
		self.files_done = 0
		self.file_name = ""
		self.host_name = socket.gethostname()

	def onDatabaseLoaded(self, callback=None):
		logger.info("...")
		self.database_loaded_callback = callback
		if self.database_loaded:
			self.onDatabaseLoadedCallback()

	def onDatabaseLoadedCallback(self):
		logger.info("...")
		if self.database_loaded_callback:
			self.database_loaded_callback()

	def onDatabaseChanged(self, callback=None):
		logger.info("...")
		self.database_changed_callback = callback

	def onDatabaseChangedCallback(self):
		if self.database_changed_callback:
			self.database_changed_callback()

	# row functions

	def execCacheOp(self, file_op, src_path, dst_dir):
		logger.info("file_op: %s, src_path: %s, dst_dir: %s", file_op, src_path, dst_dir)
		if file_op == FILE_OP_DELETE:
			afile = self.getFile("recordings", src_path)
			if afile:
				del_list = self.sqlSelect("recordings", "path LIKE ? AND file_type = ?", [src_path + "%", FILE_TYPE_FILE])
				self.addLogEntry(del_list)
				self.delete("recordings", src_path)
				self.delete("covers", os.path.basename(src_path))
			else:
				self.deleteLogEntry(src_path)
		elif file_op == FILE_OP_MOVE:
			self.move(src_path, dst_dir)
		elif file_op == FILE_OP_COPY:
			self.copy(src_path, dst_dir)

	def add(self, table, afile):
		# logger.info("table: %s, afile: %s", table, afile)
		self.sqlInsert(table, afile)

	def exists(self, path):
		afile = self.getFile("recordings", path)
		logger.debug("path: %s, afile: %s", path, afile)
		return afile is not None

	def removeEmptyDirs(self, path):
		logger.info("path: %s", path)
		empty = not self.sqlSelect("recordings", "path LIKE ?", [path + "/%"])
		while empty and path not in self.bookmarks and os.path.dirname(path) not in self.bookmarks:
			logger.debug("removing: %s", path)
			self.sqlDelete("recordings", "path = ?", [path])
			path = os.path.dirname(path)

	def delete(self, table, path):
		logger.debug("path: %s", path)
		if table == "recordings":
			afile = self.getFile(table, path)
			if afile:
				if afile[FILE_IDX_TYPE] == FILE_TYPE_DIR:
					self.sqlDelete(table, "path LIKE ?", [path + "%"])
					self.sqlDelete("covers", "path LIKE ?", [os.path.basename(path)])
				else:
					self.sqlDelete(table, "path = ?", [path])
				self.removeEmptyDirs(os.path.dirname(path))
		else:
			self.sqlDelete(table, "path LIKE ?", [path + "%"])

	def update(self, path, **kwargs):
		logger.debug("%s, kwargs: %s", path, kwargs)
		afile = self.getFile("recordings", path)
		if afile:
			afile = list(afile)
			column_keys = [column.split(" ", 1)[0] for column in self.RECORDING_COLUMNS]
			logger.debug("kwargs.items(): %s", list(kwargs.items()))
			for key, value in list(kwargs.items()):
				logger.debug("key: %s, value: %s", key, value)
				if key in column_keys:
					afile[column_keys.index(key)] = value
				else:
					logger.error("invalid column key: %s", key)
			self.add("recordings", afile)

	def updateFilePaths(self, path, afile):
		logger.info("path: %s, afile: %s", path, afile)
		afile[FILE_IDX_DIR] = os.path.dirname(path)
		afile[FILE_IDX_PATH] = path
		afile[FILE_IDX_BOOKMARK] = MountCockpit.getInstance().getBookmark("MVC", path)
		afile[FILE_IDX_RELPATH] = os.path.abspath(os.path.relpath(path, afile[FILE_IDX_BOOKMARK]))
		afile[FILE_IDX_RELDIR] = os.path.dirname(afile[FILE_IDX_RELPATH])

	def createDestinationDirs(self, src_path, dst_path):
		logger.info("src_path: %s, dst_path: %s", src_path, dst_path)
		while not self.exists(dst_path):
			logger.info("creating missing dir: %s > %s", src_path, dst_path)
			src_file = self.getFile("recordings", src_path)
			dst_file = list(src_file)
			self.updateFilePaths(dst_path, dst_file)
			self.add("recordings", dst_file)
			src_path = os.path.dirname(src_path)
			dst_path = os.path.dirname(dst_path)
			logger.debug("next: src_path: %s, dst_path: %s", src_path, dst_path)

	def copyFile(self, src_path, dst_dir):
		logger.debug("src_path: %s, dst_dir: %s", src_path, dst_dir)
		src_file = self.getFile("recordings", src_path)
		if src_file:
			dst_path = os.path.join(dst_dir, os.path.basename(src_path))
			dst_file = self.getFile("recordings", dst_path)
			if dst_file is None:
				dst_file = list(src_file)
				self.updateFilePaths(dst_path, dst_file)
				self.add("recordings", dst_file)
				self.createDestinationDirs(os.path.dirname(src_path), dst_dir)
			else:
				logger.debug("dst_path: %s already exists.", dst_path)
		else:
			logger.debug("src_path: %s does not exist.", src_path)

	def copy(self, src_path, dst_path):
		logger.debug("src_path: %s, dst_dir: %s", src_path, dst_path)
		afile = self.getFile("recordings", src_path)
		logger.debug("%s > %s", src_path, dst_path)
		self.copyFile(src_path, dst_path)
		if afile and afile[FILE_IDX_TYPE] == FILE_TYPE_DIR:
			file_list = self.sqlSelect("recordings", "path LIKE ?", [src_path + "/%"])
			for bfile in file_list:
				src_path2 = bfile[FILE_IDX_PATH]
				dst_path2 = os.path.abspath(os.path.join(dst_path, os.path.relpath(src_path2, os.path.dirname(src_path))))
				logger.debug("%s > %s", src_path2, os.path.dirname(dst_path2))
				self.copyFile(src_path2, os.path.dirname(dst_path2))

	def move(self, src_path, dst_dir):
		logger.debug("src_path: %s, dst_dir: %s", src_path, dst_dir)
		if os.path.dirname(src_path) != dst_dir:
			self.copy(src_path, dst_dir)
			self.delete("recordings", src_path)

	def getFile(self, table, path):
		logger.debug("table: %s, path: %s", table, path)
		afile = None
		file_list = self.sqlSelect(table, "path = ?", [path])
		if file_list:
			if len(file_list) == 1:
				afile = file_list[0]
			else:
				logger.error("not a single response: %s", file_list)
		return afile

	# database list functions

	def getFileList(self, adir, recursive=False):
		logger.debug("adir: %s", adir)
		file_list = []
		afile = self.getFile("recordings", adir)
		if afile:
			rel_dir = afile[FILE_IDX_RELPATH]
			logger.debug("rel_dir: %s", rel_dir)
			wildcard = "%" if recursive else ""
			where = "rel_dir LIKE ?"
			if "trashcan" not in rel_dir:
				where += " AND rel_dir NOT LIKE '%trashcan%'"
			where += " AND file_type = ?"
			file_list = self.sqlSelect("recordings", where, [rel_dir + wildcard, FILE_TYPE_FILE])
		return file_list

	def getDirList(self, adir, recursive=False, distinct=True):
		logger.debug("adir: %s", adir)
		dir_list = []
		afile = self.getFile("recordings", adir)
		if afile:
			rel_dir = afile[FILE_IDX_RELPATH]
			logger.debug("rel_dir: %s", rel_dir)
			file_types = [FILE_TYPE_DIR, FILE_TYPE_LINK]
			types = ",".join("?" * len(file_types))
			wildcard = ""
			if recursive:
				wildcard = "%" if rel_dir.endswith("/") else "/%"
			where = "path != bookmark"
			where += " AND file_name != 'trashcan'"
			where += " AND rel_dir LIKE ?"
			if "trashcan" not in rel_dir:
				where += " AND rel_dir NOT LIKE '%trashcan%'"
			where += " AND file_type IN ({})".format(types)
			dir_list = self.sqlSelect("recordings", where, [rel_dir + wildcard] + file_types)
			if distinct:
				dir_list = self.createDistinctDirList(dir_list)
		return dir_list

	def createDistinctDirList(self, alist):
		file_name_list = []
		dir_list = []
		for afile in alist:
			file_name = os.path.basename(afile[FILE_IDX_PATH])
			if file_name not in file_name_list and afile[FILE_IDX_PATH] not in self.bookmarks:
				file_name_list.append(file_name)
				dir_list.append(afile)
		logger.debug("dir_list: %s", dir_list)
		return dir_list

	def getDirNamesList(self, adir):
		logger.info("adir: %s", adir)
		file_types = [FILE_TYPE_DIR, FILE_TYPE_LINK]
		types_bindings = ",".join("?" * len(file_types))
		afile = self.getFile("recordings", adir)
		rel_path = afile[FILE_IDX_RELPATH]
		where = "file_name != 'trashcan'"
		where += " AND rel_dir = ?"
		where += " AND file_type IN ({})".format(types_bindings)
		alist = self.sqlSelectDistinct("recordings", "file_name", where, [rel_path] + file_types)
		dir_names_list = [item[0] for item in alist]
		logger.debug("dir_names_list: %s", dir_names_list)
		return dir_names_list

	def getCountSize(self, path):
		logger.info("path: %s", path)
		total_count = total_size = 0
		if not os.path.basename(path) == "..":
			afile = self.getFile("recordings", path)
			if afile:
				rel_path = afile[FILE_IDX_RELPATH]
				logger.debug("rel_path: %s", rel_path)
				file_list = self.sqlSelect("recordings", "rel_path LIKE ? AND file_type = ?", [rel_path + "%", FILE_TYPE_FILE])
				for afile in file_list:
					total_count += 1
					total_size += afile[FILE_IDX_SIZE]
		logger.debug("path: %s, total_count: %s, total_size: %s", path, total_count, total_size)
		return total_count, total_size

	def getSortMode(self, adir):
		logger.info("adir: %s", adir)
		sort = ""
		timestamp = 0
		afile = self.getFile("recordings", adir)
		if afile:
			rel_path = afile[FILE_IDX_RELPATH]
			where = "rel_path = ?"
			where += " AND file_type = ?"
			alist = self.sqlSelect("recordings", where, [rel_path, FILE_TYPE_DIR])
			for afile in alist:
				data = afile[FILE_IDX_SORT].split(",")
				if len(data) > 1 and int(data[0]) > timestamp:
					sort = data[1]
					timestamp = int(data[0])
		if not sort:
			logger.debug("using default sort")
			sort = config.plugins.moviecockpit.list_sort.value
		logger.debug("sort: %s", sort)
		return sort

	# database functions

	def closeDatabase(self):
		logger.debug("...")
		self.sqlClose()

	def clearDatabase(self):
		logger.debug("...")
		self.sqlClearTable("recordings")
		self.sqlClearTable("covers")
		self.database_loaded = False

	# database load functions

	def getProgress(self):
		logger.debug("files_total: %s, files_done: %s", self.files_total, self.files_done)
		percent = 100
		if self.files_total:
			percent = int(float(self.files_done) / float(self.files_total) * 100)
		return self.files_total - self.files_done, self.file_name, FILE_OP_LOAD, percent

	def loadDatabase(self, dirs=None):
		self.database_loaded = False
		if dirs is None:
			self.bookmarks = MountCockpit.getInstance().getMountedBookmarks("MVC")
			dirs = self.bookmarks
		logger.info("dirs: %s", dirs)
		if dirs:
			self.clearDatabase()
			self.load_list = self.getDirsLoadList(dirs)
			self.files_total = len(self.load_list)
			self.files_done = 0
			self.file_name = ""
			DelayTimer(10, self.nextFileOp)

	def nextFileOp(self):
		logger.info("...")
		if self.load_list:
			path = self.load_list.pop(0)
			self.file_name = os.path.basename(path)
			self.loadDatabaseFile(path)
			self.files_done += 1
			DelayTimer(10, self.nextFileOp)
		else:
			logger.debug("done.")
			self.database_loaded = True
			self.onDatabaseLoadedCallback()

	def loadDatabaseCover(self, path):
		logger.info("path: %s", path)
		afile = self.newCoverData(path)
		if afile:
			self.add("covers", afile)

	def loadDatabaseFile(self, path):
		logger.info("path: %s", path)
		afile = ()
		if os.path.isfile(path):
			afile = self.newFileData(path)
		elif os.path.islink(path):
			afile = self.newDirData(path, FILE_TYPE_LINK)
		elif os.path.isdir(path):
			afile = self.newDirData(path, FILE_TYPE_DIR)
		if afile:
			self.add("recordings", afile)
			self.loadDatabaseCover(path)
			if self.database_loaded:
				self.onDatabaseChangedCallback()

	def newCoverData(self, path):
		logger.info("path: %s", path)
		logger.debug("trying: %s", os.path.splitext(path)[0] + ".jpg")
		afile = None
		cover = readFile(os.path.splitext(path)[0] + ".jpg")
		if cover:
			cover_name = os.path.basename(path)
			afile = (cover_name, cover)
		else:
			cover_name = os.path.basename(path)
			cover_path = os.path.join(path, cover_name + ".jpg")
			logger.debug("trying: %s", cover_path)
			cover = readFile(cover_path)
			if cover:
				afile = (cover_name, cover)
		if afile:
			logger.debug("found cover_name: %s", cover_name)
		return afile

	def newDirData(self, path, file_type):
		logger.info("path: %s, file_type: %s", path, file_type)
		name = os.path.basename(path)
		sort = ""
		if name != "..":
			sort_path = os.path.join(path, ".sort")
			if os.path.exists(sort_path):
				sort = readFile(sort_path).strip("\n")
		afile = self.sqlInitFile()
		afile[FILE_IDX_TYPE] = file_type
		afile[FILE_IDX_BOOKMARK] = MountCockpit.getInstance().getBookmark("MVC", path)
		afile[FILE_IDX_PATH] = path
		afile[FILE_IDX_RELPATH] = os.path.abspath(os.path.relpath(path, afile[FILE_IDX_BOOKMARK]))
		afile[FILE_IDX_DIR] = os.path.dirname(path)
		afile[FILE_IDX_RELDIR] = os.path.dirname(afile[FILE_IDX_RELPATH])
		afile[FILE_IDX_FILENAME] = os.path.basename(path)
		afile[FILE_IDX_NAME] = afile[FILE_IDX_FILENAME]
		afile[FILE_IDX_LENGTH] = -1
		afile[FILE_IDX_SORT] = sort
		afile[FILE_IDX_HOSTNAME] = self.host_name
		# logger.debug("afile: %s", afile)
		return tuple(afile)

	def newFileData(self, path):

		def parseFilename(file_name):
			name = file_name
			service_name = ""
			start_time = 0
			words = file_name.split(" - ", 2)
			date_string = words[0]
			if date_string[0:8].isdigit() and date_string[8] == " " and date_string[9:13].isdigit():
				# Default: file_name = YYYYMMDD TIME - service_name
				dt = datetime.strptime(date_string, '%Y%m%d %H%M')
				start_time = int(time.mktime(dt.timetuple()))
			if len(words) > 1:
				service_name = words[1]
			if len(words) > 2:
				name = words[2]
			cutno = ""
			if name[-4] == "_" and name[-3:].isdigit():
				cutno = name[-3:]
				name = name[:-4]
			logger.debug("file_name: %s, start_time: %s, service_name: %s, name: %s, cutno: %s", file_name, start_time, service_name, name, cutno)
			return start_time, service_name, name, cutno

		def getEitStartLength(eit, recording_start_time, recording_stop_time, recording_margin_before, recording_margin_after):
			logger.debug("recording_start_time: %s, recording_stop_time: %s, recording_margin_before: %s, recording_margin_after: %s", datetime.fromtimestamp(recording_start_time), datetime.fromtimestamp(recording_stop_time), recording_margin_before, recording_margin_after)
			event_start_time = eit["start"]
			event_length = eit["length"]
			event_end_time = event_start_time + event_length
			start = event_start_time
			length = event_length
			if recording_start_time:
				if recording_start_time >= event_end_time:
					start = recording_start_time + recording_margin_before
					length = recording_stop_time - recording_start_time - recording_margin_before - recording_margin_after
					logger.debug("start 1: ee rs: %s, %s", start, length)
				elif recording_start_time >= event_start_time:
					start = recording_start_time
					length = event_length - (recording_start_time - event_start_time)
					logger.debug("start 2: es rs: %s, %s", start, length)
			if recording_stop_time:
				if recording_stop_time <= event_end_time:
					if recording_start_time >= event_start_time:
						start = recording_start_time
						length -= event_end_time - recording_stop_time
						logger.debug("stop 1a: es re ee: %s, %s", start, length)
					else:
						start = event_start_time
						length = recording_stop_time - event_start_time
						logger.debug("stop 1b: re es: %s, %s", start, length)
			logger.debug("start: %s, length: %s", datetime.fromtimestamp(start), length)
			return start, length

		def getMetaStartLength(_meta, recording_start_time, recording_stop_time):
			logger.info("recording_start_time: %s, recording_stop_time: %s", datetime.fromtimestamp(recording_start_time), datetime.fromtimestamp(recording_stop_time))
			length = 0
			if recording_start_time and recording_stop_time:
				length = recording_stop_time - recording_start_time
			logger.debug("start_time: %s, length: %s", datetime.fromtimestamp(recording_start_time), length)
			return recording_start_time, length

		logger.info("path: %s", path)
		file_path, ext = os.path.splitext(path)
		file_name = os.path.basename(file_path)
		file_dir = os.path.dirname(file_path)
		name = file_name
		short_description, extended_description, service_reference, sort = "", "", "", ""
		length = 0
		cuts = cPickle.dumps(unpackCutList(readFile(path + ".cuts")))
		event_start_time = recording_stop_time = recording_start_time = int(os.stat(path).st_ctime)
		size = os.path.getsize(path)

		if ext in EXT_TS:
			start_time, _service_name, name, cutno = parseFilename(file_name)
			if start_time:
				event_start_time = start_time
			recording_margin_before = config.recording.margin_before.value * 60
			recording_margin_after = config.recording.margin_after.value * 60
			meta = ParserMetaFile(path).getMeta()
			if meta:
				name = meta["name"]
				service_reference = meta["service_reference"]
				recording_start_time = meta["recording_start_time"]
				recording_stop_time = meta["recording_stop_time"]
				if "recording_margin_before" in meta and meta["recording_margin_before"]:
					recording_margin_before = meta["recording_margin_before"]
				if "recording_margin_after" in meta and meta["recording_margin_after"]:
					recording_margin_after = meta["recording_margin_after"]
				event_start_time, length = getMetaStartLength(meta, recording_start_time, recording_stop_time)
			eit = ParserEitFile(path, self.epglang).getEit()
			if eit:
				name = eit["name"]
				if name.startswith("FilmMittwoch im Ersten: "):
					name = name[len("FilmMittwoch im Ersten: "):]
				event_start_time, length = getEitStartLength(eit, recording_start_time, recording_stop_time, recording_margin_before, recording_margin_after)
				short_description = eit["short_description"]
				extended_description = eit["description"]
			if not meta and not eit:
				length = 0
				recording_start_time = int(os.stat(path).st_ctime)
				event_start_time = recording_start_time
			if cutno:
				name = "%s (%s)" % (name, cutno)
		else:
			length = getFfprobeDuration(path)

		txt_path = os.path.splitext(path)[0] + ".txt"
		if os.path.exists(txt_path):
			extended_description = readFile(txt_path)

		logger.debug("path: %s, name: %s, event_start_time %s, length: %s, cuts: %s", path, name, datetime.fromtimestamp(event_start_time), length, cuts)

		afile = self.sqlInitFile()
		afile[FILE_IDX_TYPE] = FILE_TYPE_FILE
		afile[FILE_IDX_BOOKMARK] = MountCockpit.getInstance().getBookmark("MVC", path)
		afile[FILE_IDX_PATH] = path
		afile[FILE_IDX_RELPATH] = os.path.abspath(os.path.relpath(path, afile[FILE_IDX_BOOKMARK]))
		afile[FILE_IDX_DIR] = file_dir
		afile[FILE_IDX_RELDIR] = os.path.dirname(afile[FILE_IDX_RELPATH])
		afile[FILE_IDX_FILENAME] = file_name
		afile[FILE_IDX_EXT] = ext
		afile[FILE_IDX_NAME] = name
		afile[FILE_IDX_EVENT_START_TIME] = event_start_time
		afile[FILE_IDX_RECORDING_START_TIME] = recording_start_time
		afile[FILE_IDX_RECORDING_STOP_TIME] = recording_stop_time
		afile[FILE_IDX_LENGTH] = length
		afile[FILE_IDX_DESCRIPTION] = short_description
		afile[FILE_IDX_EXTENDED_DESCRIPTION] = extended_description
		afile[FILE_IDX_SERVICE_REFERENCE] = service_reference
		afile[FILE_IDX_SIZE] = size
		afile[FILE_IDX_CUTS] = cuts
		afile[FILE_IDX_SORT] = sort
		afile[FILE_IDX_HOSTNAME] = self.host_name
		# logger.debug("afile: %s", afile]
		return tuple(afile)

	# database load list functions

	def __getDirLoadList(self, adir):
		logger.debug("adir: %s", adir)
		load_list = []
		if os.path.exists(adir):
			walk_listdir = os.listdir(adir)
			for walk_name in walk_listdir:
				path = os.path.join(adir, walk_name)
				if os.path.isfile(path):
					ext = os.path.splitext(path)[1]
					if ext in ALL_VIDEO:
						load_list.append(path)
				else:
					load_list.append(path)
					load_list += self.__getDirLoadList(path)
		else:
			logger.error("adir does not exist: %s", adir)
		return load_list

	def getDirsLoadList(self, dirs):
		logger.info("dirs: %s", dirs)
		load_list = []
		for adir in dirs:
			load_list.append(adir)
			load_list += self.__getDirLoadList(adir)
		return load_list

	# others

	def getRecordings(self):
		logger.info("...")
		return getRecordings()
