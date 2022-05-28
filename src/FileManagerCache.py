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


import os
import time
from Debug import logger
from Components.config import config
from FileManagerCacheSQL import FileManagerCacheSQL
from datetime import datetime
from ParserEitFile import ParserEitFile
from ParserMetaFile import ParserMetaFile
from CutListUtils import unpackCutList, ptsToSeconds, getCutListLength
from ServiceUtils import EXT_TS, ALL_VIDEO
from FileUtils import readFile, deleteFile
from DelayTimer import DelayTimer
from UnicodeUtils import convertToUtf8
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from FileManagerUtils import SQL_DB_NAME, FILE_TYPE_FILE, FILE_IDX_TYPE, FILE_TYPE_DIR, FILE_TYPE_LINK, FILE_IDX_DIR, FILE_IDX_PATH, FILE_IDX_FILENAME, FILE_IDX_SIZE
from FileManagerUtils import FILE_OP_LOAD, FILE_OP_DELETE, FILE_OP_MOVE, FILE_OP_COPY


class FileManagerCache(FileManagerCacheSQL):

	def __init__(self):
		logger.info("...")
		self.database_loaded = False
		self.database_loaded_callback = None
		self.database_changed_callback = None
		FileManagerCacheSQL.__init__(self)
		self.epglang = config.plugins.moviecockpit.epglang.value
		self.bookmarks = MountCockpit.getInstance().getMountedBookmarks("MVC")
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

	### row functions

	def execCacheOp(self, file_op, src_path, dst_dir):
		logger.info("file_op: %s, src_path: %s, dst_dir: %s", file_op, src_path, dst_dir)
		if file_op == FILE_OP_DELETE:
			self.delete("recordings", src_path)
			self.delete("covers", src_path)
		elif file_op == FILE_OP_MOVE:
			self.move(src_path, dst_dir)
		elif file_op == FILE_OP_COPY:
			self.copy(src_path, dst_dir)

	def add(self, table, afile):
		#logger.info("table: %s, afile: %s", table, afile)
		self.sqlInsert(table, afile)

	def exists(self, path):
		afile = self.getFile("recordings", path)
		logger.debug("path: %s, afile: %s", path, afile)
		return afile is not None

	def delete(self, table, path):
		logger.debug("path: %s", path)
		if table == "recordings":
			where = "path LIKE ?"
		else:
			where = "file_name LIKE ?"
			path = os.path.basename(path)
		self.sqlDelete(table, where, [path + "%"])

	def update(self, path, **kwargs):
		logger.debug("%s, kwargs: %s", path, kwargs)
		afile = self.getFile("recordings", path)
		if afile:
			afile = list(afile)
			column_keys = [column.split(" ", 1)[0] for column in self.RECORDING_COLUMNS]
			logger.debug("kwargs.items(): %s", kwargs.items())
			for key, value in kwargs.items():
				logger.debug("key: %s, value: %s", key, value)
				if key in column_keys:
					afile[column_keys.index(key)] = value
				else:
					logger.error("invalid column key: %s", key)
			self.add("recordings", afile)

	def copy(self, src_path, dst_dir):
		logger.debug("src_path: %s, dst_dir: %s", src_path, dst_dir)
		if not self.exists(dst_dir):
			afile = self.newDirData(dst_dir)
			self.add("recordings", afile)
		file_list = self.sqlSelect("recordings", "path LIKE ?", [src_path + "%"])
		for afile in file_list:
			logger.debug("afile: %s", afile)
			path = afile[FILE_IDX_PATH]
			dst_path = os.path.join(dst_dir, path[len(os.path.dirname(src_path)) + 1:])
			dst_file = self.getFile("recordings", dst_path)
			if dst_file is None:
				dst_file = list(afile)
				dst_file[FILE_IDX_DIR] = os.path.dirname(dst_path)
				dst_file[FILE_IDX_PATH] = dst_path
				self.add("recordings", dst_file)
			else:
				logger.error("file already exists at destination: %s", dst_path)

	def move(self, src_path, dst_dir):
		logger.debug("src_path: %s, dst_dir: %s", src_path, dst_dir)
		if os.path.dirname(src_path) != dst_dir:
			self.copy(src_path, dst_dir)
			self.delete("recordings", src_path)

	def getFile(self, table, path):
		logger.debug("table: %s, path: %s", table, path)
		afile = None
		if table == "recordings":
			file_list = self.sqlSelect(table, "path = ?", [path])
		else:
			file_list = self.sqlSelect(table, "file_name = ?", [os.path.basename(path)])
		if file_list:
			if len(file_list) == 1:
				afile = file_list[0]
			else:
				logger.error("not a single response: %s", str(file_list))
		return afile

	### database list functions

	def getFileList(self, dirs):
		logger.debug("dirs: %s", dirs)
		file_list = []
		if dirs:
			binds = ",".join("?" * len(dirs))
			where = "directory IN ({})".format(binds)
			where += " AND file_type = %d" % FILE_TYPE_FILE
			file_list = self.sqlSelect("recordings", where, dirs)
		return file_list

	def getDirList(self, dirs):
		logger.debug("dirs: %s", dirs)
		dirs_list = []
		if dirs:
			binds = ",".join("?" * len(dirs))
			where = "directory IN ({})".format(binds)
			where += " AND file_name != 'trashcan'"
			where += " AND file_name != '..'"
			where += " AND file_type != %d" % FILE_TYPE_FILE
			dirs_list = self.sqlSelect("recordings", where, dirs)

		file_name_list = []
		dir_list = []
		for afile in dirs_list:
			file_name = afile[FILE_IDX_FILENAME]
			if file_name not in file_name_list:
				file_name_list.append(file_name)
				dir_list.append(afile)
		logger.debug("dir_list: %s", dir_list)
		return dir_list

	def getCountSize(self, path):
		total_count = total_size = 0
		all_dirs = MountCockpit.getInstance().getVirtualDirs("MVC", [path])
		for adir in all_dirs:
			file_list = self.sqlSelect("recordings", "path LIKE ? AND file_type = ?", [adir + "%", FILE_TYPE_FILE])
			for afile in file_list:
				logger.debug("apath: %s, afile_type: %s", afile[FILE_IDX_PATH], afile[FILE_IDX_TYPE])
				total_count += 1
				total_size += afile[FILE_IDX_SIZE]
		logger.debug("path: %s, total_count: %s, total_size: %s", path, total_count, total_size)
		return total_count, total_size

	### database functions

	def closeDatabase(self):
		logger.debug("...")
		self.sqlClose()

	def clearDatabase(self):
		logger.debug("...")
		self.sqlClearTable("recordings")
		self.sqlClearTable("covers")
		self.database_loaded = False

	### database load functions

	def getProgress(self):
		logger.debug("files_total: %s, files_done: %s", self.files_total, self.files_done)
		percent = 100
		if self.files_total:
			percent = self.files_done / self.files_total * 100
		return self.files_total - self.files_done, self.file_name, FILE_OP_LOAD, percent

	def loadDatabase(self, dirs=None):
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
		self.add("covers", afile)

	def loadDatabaseFile(self, path):
		logger.info("path: %s", path)
		if os.path.isfile(path):
			afile = self.newFileData(path)
			self.add("recordings", afile)
			afile = self.newCoverData(path)
			self.add("covers", afile)
		else:
			if os.path.islink(path):
				afile = self.newLinkData(path)
				self.add("recordings", afile)
			elif os.path.isdir(path):
				afile = self.newDirData(path)
				self.add("recordings", afile)
			if not MountCockpit.getInstance().isBookmark(path):
				afile = self.newDirData(os.path.join(path, ".."))
				self.add("recordings", afile)
		if self.database_loaded:
			self.onDatabaseChangedCallback()

	def newCoverData(self, path):
		logger.info("path: %s", path)
		cover = readFile(os.path.splitext(path)[0] + ".jpg")
		return (os.path.basename(path), cover)

	def newDirData(self, path):
		logger.info("path: %s", path)
		ext, short_description, extended_description, service_reference, cuts, tags = "", "", "", "", "", ""
		size = length = event_start_time = recording_start_time = recording_stop_time = 0
		name = convertToUtf8(os.path.basename(path))
		return (os.path.dirname(path), FILE_TYPE_DIR, path, os.path.basename(path), ext, name, event_start_time, recording_start_time, recording_stop_time, length, short_description, extended_description, service_reference, size, cuts, tags)

	def newLinkData(self, path):
		logger.info("path: %s", path)
		ext, short_description, extended_description, service_reference, cuts, tags = "", "", "", "", "", ""
		size = length = event_start_time = recording_start_time = recording_stop_time = 0
		name = convertToUtf8(os.path.basename(path))
		return (os.path.dirname(path), FILE_TYPE_LINK, path, os.path.basename(path), ext, name, event_start_time, recording_start_time, recording_stop_time, length, short_description, extended_description, service_reference, size, cuts, tags)

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

		def getEitStartLength(eit, recording_start_time, recording_stop_time):
			logger.debug("recording_start_time: %s, recording_stop_time: %s", datetime.fromtimestamp(recording_start_time), datetime.fromtimestamp(recording_stop_time))
			event_start_time = eit["start"]
			length = eit["length"]
			if recording_start_time:
				if recording_start_time > event_start_time:
					length -= recording_start_time - event_start_time
					event_start_time = recording_start_time
			if recording_stop_time:
				if event_start_time <= recording_stop_time <= event_start_time + length:
					length = recording_stop_time - event_start_time
				elif recording_stop_time < event_start_time:
					length = 0
			logger.debug("event_start_time: %s, length: %s", datetime.fromtimestamp(event_start_time), length)
			return event_start_time, length

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
		name = convertToUtf8(file_name)
		short_description, extended_description, service_reference, tags = "", "", "", ""
		length = 0
		cuts = readFile(path + ".cuts")
		event_start_time = recording_stop_time = recording_start_time = 0
		size = os.path.getsize(path)

		if ext in EXT_TS:
			start_time, _service_name, name, cutno = parseFilename(file_name)
			if start_time:
				event_start_time = start_time
			meta = ParserMetaFile(path).getMeta()
			if meta:
				name = meta["name"]
				service_reference = meta["service_reference"]
				tags = meta["tags"]
				recording_start_time = meta["recording_start_time"]
				recording_stop_time = meta["recording_stop_time"]
				event_start_time, length = getMetaStartLength(meta, recording_start_time, recording_stop_time)
			eit = ParserEitFile(path, self.epglang).getEit()
			if eit:
				name = eit["name"]
				if name.startswith("FilmMittwoch im Ersten: "):
					name = name[len("FilmMittwoch im Ersten: "):]
				event_start_time, length = getEitStartLength(eit, recording_start_time, recording_stop_time)
				short_description = eit["short_description"]
				extended_description = eit["description"]
			if not meta and not eit:
				length = 0
				recording_start_time = int(os.stat(path).st_ctime)
				event_start_time = recording_start_time
			if cutno:
				name = "%s (%s)" % (name, cutno)
		else:
			length = ptsToSeconds(getCutListLength(unpackCutList(cuts)))

		logger.debug("path: %s, name: %s, event_start_time %s, length: %s", path, name, datetime.fromtimestamp(event_start_time), length)
		return (file_dir, FILE_TYPE_FILE, path, file_name, ext, name, event_start_time, recording_start_time, recording_stop_time, length, short_description, extended_description, service_reference, size, cuts, tags)

	### database load list functions

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
			load_list += self.__getDirLoadList(adir)
		return load_list
