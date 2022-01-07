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


from Debug import logger
import os
import time
from FileCacheSQL import FileCacheSQL
from datetime import datetime
from ParserEitFile import ParserEitFile
from ParserMetaFile import ParserMetaFile
from CutListUtils import unpackCutList, ptsToSeconds, getCutListLength
from ServiceUtils import EXT_TS, EXT_VIDEO
from FileUtils import readFile, deleteFile
from DelayTimer import DelayTimer
from UnicodeUtils import convertToUtf8
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from Tools.BoundFunction import boundFunction
from FileCacheUtils import SQL_DB_NAME, FILE_TYPE_FILE, FILE_TYPE_DIR


instance = None


class FileCache(FileCacheSQL):

	def __init__(self):
		logger.info("...")
		self.database_loaded = False
		self.database_loaded_callback = None
		self.database_changed_callback = None
		FileCacheSQL.__init__(self)
		self.bookmarks = MountCockpit.getInstance().getMountedBookmarks("MVC")
		if not os.path.exists(SQL_DB_NAME) or os.path.exists("/etc/enigma2/.cachecockpit"):
			logger.info("loading database...")
			deleteFile("/etc/enigma2/.cachecockpit")
			MountCockpit.getInstance().onInitComplete(boundFunction(self.loadDatabase))
		else:
			logger.info("database is already loaded.")
			self.database_loaded = True

	@staticmethod
	def getInstance():
		global instance
		if instance is None:
			instance = FileCache()
		return instance

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
		logger.info("..")
		self.database_changed_callback = callback

	def onDatabaseChangedCallback(self):
		if self.database_changed_callback:
			self.database_changed_callback()

### cache functions

	def add(self, file_data):
		self.sqlInsert(file_data)

	### database row functions

	def exists(self, path):
		file_data = self.getFile(path)
		logger.debug("path: %s, file_data: %s", path, str(file_data))
		return file_data is not None

	def delete(self, path, file_type=FILE_TYPE_FILE):
		logger.debug("file_type: %s, path: %s", file_type, path)
		where = "path LIKE ?"
		self.sqlDelete(where, [path + "%"])

	def update(self, path, **kwargs):
		logger.debug("%s, kwargs: %s", path, kwargs)
		file_data = self.getFile(path)
		if file_data:
			self.directory, self.file_type, self.path, self.file_name, self.ext, self.name, self.event_start_time, self.recording_start_time, self.recording_stop_time, self.length, self.description, self.extended_description, self.service_reference, self.size, self.cuts, self.tags = file_data
			logger.debug("kwargs.items(): %s", kwargs.items())
			for key, value in kwargs.items():
				logger.debug("key: %s, value: %s", key, value)
				setattr(self, key, value)
			self.add((self.directory, self.file_type, self.path, self.file_name, self.ext, self.name, self.event_start_time, self.recording_start_time, self.recording_stop_time, self.length, self.description, self.extended_description, self.service_reference, self.size, self.cuts, self.tags))

	def copy(self, src_path, dst_dir, file_type=FILE_TYPE_FILE):
		logger.debug("src_path: %s, dst_dir: %s, file_type: %s", src_path, dst_dir, file_type)
		file_list = self.sqlSelect("path LIKE ?", [src_path + "%"])
		for file_data in file_list:
			_directory, file_type, path, file_name, ext, name, event_start_time, recording_start_time, recording_stop_time, length, description, extended_description, service_reference, size, cuts, tags = file_data
			dst_path = os.path.join(dst_dir, path[len(os.path.dirname(src_path)) + 1:])
			dest_file = self.getFile(dst_path)
			if dest_file is None:
				self.add((os.path.dirname(dst_path), file_type, dst_path, file_name, ext, name, event_start_time, recording_start_time, recording_stop_time, length, description, extended_description, service_reference, size, cuts, tags))
			else:
				logger.error("file already exists at destination: %s", dst_path)

	def move(self, src_path, dest_dir, file_type=FILE_TYPE_FILE):
		logger.debug("src_path: %s, dest_dir: %s, file_type: %s", src_path, dest_dir, file_type)
		if os.path.dirname(src_path) != dest_dir:
			self.copy(src_path, dest_dir, file_type)
			self.delete(src_path, file_type)

	def getFile(self, path):
		logger.debug("path: %s", path)
		file_list = self.sqlSelect("path = ?", [path])
		file_data = None
		if file_list:
			if len(file_list) == 1:
				file_data = file_list[0]
			else:
				logger.error("not a single response: %s", str(file_list))
		return file_data

	def __resolveVirtualDirs(self, dirs):
		logger.debug("dirs: %s", dirs)
		self.bookmarks = MountCockpit.getInstance().getMountedBookmarks("MVC")
		all_dirs = []
		for adir in dirs:
			if adir in self.bookmarks:
				for bookmark in self.bookmarks:
					if bookmark not in all_dirs:
						all_dirs.append(bookmark)
			elif os.path.basename(adir) == "trashcan":
				for bookmark in self.bookmarks:
					trashcan_dir = bookmark + "/trashcan"
					if trashcan_dir not in all_dirs:
						all_dirs.append(trashcan_dir)
			else:
				if adir not in all_dirs:
					all_dirs.append(adir)

		logger.debug("all_dirs: %s", all_dirs)
		return all_dirs

	def getFileList(self, dirs, include_all_dirs=True):
		logger.debug("dirs: %s", dirs)
		file_list = []
		all_dirs = self.__resolveVirtualDirs(dirs) if include_all_dirs else dirs
		if all_dirs:
			binds = ",".join("?" * len(all_dirs))
			where = "directory IN ({})".format(binds)
			where += " AND file_type = %d" % FILE_TYPE_FILE
			file_list = self.sqlSelect(where, all_dirs)
		return file_list

	def getDirList(self, dirs, include_all_dirs=True):
		logger.debug("dirs: %s", dirs)
		dir_list = []
		all_dirs = self.__resolveVirtualDirs(dirs) if include_all_dirs else dirs
		if all_dirs:
			binds = ",".join("?" * len(all_dirs))
			where = "directory IN ({})".format(binds)
			where += " AND file_name != 'trashcan'"
			where += " AND file_name != '..'"
			where += " AND file_type > %d" % FILE_TYPE_FILE
			dir_list = self.sqlSelect(where, all_dirs)
		return dir_list

	def getCountSize(self, apath):
		total_count = total_size = 0
		all_dirs = self.__resolveVirtualDirs([apath])
		for adir in all_dirs:
			file_list = self.sqlSelect("path LIKE ? AND file_type = ?", [adir + "%", FILE_TYPE_FILE])
			for _directory, file_type, path, _file_name, _ext, _name, _event_start_time, _recording_start_time, _recording_stop_time, _length, _description, _extended_description, _service_reference, size, _cuts, _tags in file_list:
				logger.debug("path: %s, file_type: %s", path, file_type)
				total_count += 1
				total_size += size
		logger.debug("apath: %s, total_count: %s, total_size: %s", apath, total_count, total_size)
		return total_count, total_size

	### database functions

	def closeDatabase(self):
		logger.debug("...")
		self.sqlClose()

	def clearDatabase(self):
		logger.debug("...")
		self.sqlClearTable()

	def loadDatabase(self, dirs=None):
		if dirs is None:
			self.bookmarks = MountCockpit.getInstance().getMountedBookmarks("MVC")
			dirs = self.bookmarks
		logger.info("dirs: %s", dirs)
		if dirs:
			self.clearDatabase()
			self.load_list = self.getDirsLoadList(dirs)
			DelayTimer(10, self.nextFileOp)

	def nextFileOp(self):
		logger.debug("...")
		if self.load_list:
			path, file_type = self.load_list.pop(0)
			self.loadDatabaseFile(path, file_type)
			DelayTimer(10, self.nextFileOp)
		else:
			logger.debug("done.")
			self.database_loaded = True
			self.onDatabaseLoadedCallback()

	### database load file/dir functions

	def loadDatabaseFile(self, path, file_type=FILE_TYPE_FILE):
		logger.debug("path: %s, file_type: %s", path, file_type)
		if file_type == FILE_TYPE_FILE:
			file_data = self.newFileData(path)
			self.sqlInsert(file_data)
		elif file_type == FILE_TYPE_DIR:
			file_data = self.newDirData(path)
			self.sqlInsert(file_data)
			if path not in self.bookmarks:
				file_data = self.newDirData(os.path.join(path, ".."))
				self.sqlInsert(file_data)
		if self.database_loaded:
			self.onDatabaseChangedCallback()

	def newDirData(self, path):
		logger.debug("path: %s", path)
		ext, short_description, extended_description, service_reference, cuts, tags = "", "", "", "", "", ""
		size = length = recording_start_time = recording_stop_time = 0
		event_start_time = int(os.stat(path).st_ctime)
		name = convertToUtf8(os.path.basename(path))
		return (os.path.dirname(path), FILE_TYPE_DIR, path, os.path.basename(path), ext, name, event_start_time, recording_start_time, recording_stop_time, length, short_description, extended_description, service_reference, size, cuts, tags)

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
			if name[-4:-3] == "_" and name[-3:].isdigit():
				cutno = name[-3:]
				name = name[:-4]

			logger.debug("file_name: %s, start_time: %s, service_name: %s, name: %s, cutno: %s", file_name, start_time, service_name, name, cutno)
			return start_time, service_name, name, cutno

		def getEitData(eit, recording_start_time, recording_stop_time):
			logger.debug("recording_start_time: %s, recording_stop_time: %s", recording_start_time, recording_stop_time)
			name = eit["name"]
			event_start_time = eit["start"]
			length = eit["length"]
			short_description = eit["short_description"]
			extended_description = eit["description"]
			if recording_start_time:
				if recording_start_time > event_start_time:
					length -= recording_start_time - event_start_time
					event_start_time = recording_start_time
			if recording_stop_time:
				if event_start_time <= recording_stop_time <= event_start_time + length:
					length = recording_stop_time - event_start_time
				elif recording_stop_time < event_start_time:
					length = 0
			logger.debug("event_start_time: %s, length: %s", event_start_time, length)
			return name, event_start_time, length, short_description, extended_description

		def getMetaData(meta, recording_start_time, recording_stop_time, timer_start_time, timer_stop_time):
			logger.info("recording_start_time: %s, recording_stop_time: %s, timer_start_time: %s, timer_stop_time: %s", recording_start_time, recording_stop_time, timer_start_time, timer_stop_time)
			name = meta["name"]
			start_time = meta["rec_time"]
			if meta["recording_margin_before"]:
				start_time += meta["recording_margin_before"]
			length = 0
			short_description = ""
			extended_description = ""

			if timer_start_time and timer_stop_time:
				start = timer_start_time
				stop = timer_stop_time
				if recording_start_time and recording_start_time > timer_start_time:
					start = recording_start_time
				if start <= recording_stop_time <= timer_stop_time:
					stop = recording_stop_time
				length = stop - start
			logger.debug("start_time: %s, length: %s", start_time, length)
			return name, start_time, length, short_description, extended_description

		logger.debug("path: %s", path)
		filepath, ext = os.path.splitext(path)
		file_name = os.path.basename(filepath)
		name = convertToUtf8(os.path.basename(file_name))
		short_description, extended_description, service_reference, tags = "", "", "", ""
		length = size = 0
		cuts = readFile(path + ".cuts")
		event_start_time = recording_stop_time = recording_start_time = int(os.stat(path).st_ctime)
		size = os.path.getsize(path)

		if ext in EXT_TS:
			start_time, _service_name, name, cutno = parseFilename(file_name)
			logger.debug("start_time: %s, service_name: %s, file_name: %s, cutno: %s", start_time, _service_name, file_name, cutno)
			if start_time:
				event_start_time = start_time
			meta = ParserMetaFile(path).getMeta()
			meta_name = meta["name"]
			if meta_name:
				name = meta_name
			eit = ParserEitFile(path).getEit()
			eit_name = eit["name"]
			if eit_name:
				name = eit_name

			if eit_name and meta_name:
				service_reference = meta["service_reference"]
				tags = meta["tags"]
				recording_start_time = meta["recording_start_time"]
				recording_stop_time = meta["recording_stop_time"]
				timer_start_time = meta["timer_start_time"]
				timer_stop_time = meta["timer_stop_time"]

				eit_event_start_time = eit["start"]

				if timer_stop_time and eit_event_start_time and eit_event_start_time >= timer_stop_time:
					data = getMetaData(meta, recording_start_time, recording_stop_time, timer_start_time, timer_stop_time)
				else:
					data = getEitData(eit, recording_start_time, recording_stop_time)
				name, event_start_time, length, short_description, extended_description = data
			if cutno:
				name = "%s (%s)" % (name, cutno)
		else:
			length = ptsToSeconds(getCutListLength(unpackCutList(cuts)))

		logger.debug("path: %s, name: %s, event_start_time %s, length: %s", path, name, datetime.fromtimestamp(event_start_time), length)
		return (os.path.dirname(path), FILE_TYPE_FILE, path, file_name, ext, name, event_start_time, recording_start_time, recording_stop_time, length, short_description, extended_description, service_reference, size, cuts, tags)

	### database load list functions

	def __getDirLoadList(self, adir):
		logger.debug("adir: %s", adir)
		load_list = []
		try:
			walk_listdir = os.listdir(adir)
		except Exception:
			walk_listdir = []
		for walk_name in walk_listdir:
			path = os.path.join(adir, walk_name)
			if os.path.islink(path):
				path = os.path.realpath(path)
			if os.path.isfile(path):
				ext = os.path.splitext(path)[1]
				if ext in EXT_VIDEO:
					load_list.append((path, FILE_TYPE_FILE))
			elif os.path.isdir(path):
				load_list.append((path, FILE_TYPE_DIR))
				load_list += self.__getDirLoadList(path)
		return load_list

	def getDirsLoadList(self, dirs):
		logger.info("dirs: %s", dirs)
		load_list = []
		for adir in dirs:
			if os.path.exists(adir):
				load_list += self.__getDirLoadList(adir)
			else:
				logger.error("adir: %s", adir)
		return load_list
