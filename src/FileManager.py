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
from time import time
from Components.config import config
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from Plugins.SystemPlugins.MountCockpit.MountUtils import getBookmarkSpaceInfo
from .Debug import logger
from .FileManagerUtils import FILE_TYPE_FILE
from .FileManagerUtils import FILE_IDX_TYPE, FILE_IDX_PATH, FILE_IDX_RELPATH
from .FileManagerUtils import FILE_OP_DELETE, FILE_OP_MOVE, FILE_OP_COPY, FILE_OP_FSTRIM, FILE_OP_ERROR_NONE, FILE_OP_ERROR_NO_DISKSPACE
from .RecordingUtils import isRecording
from .FileManagerJob import FileManagerJob
from .SourceSelector import SourceSelector
from .PathUtils import getArchiveTarget, getMoveTarget, getMoveToTrashcanTarget


instance = None


class FileManager(FileManagerJob):

	def __init__(self):
		FileManagerJob.__init__(self)
		self.source_selector = SourceSelector(self)

	@staticmethod
	def getInstance():
		global instance
		if instance is None:
			instance = FileManager()
		return instance

	def execFileOp(self, file_op, path, target_dir=None, file_op_callback=None):

		def checkFreeSpace(path, target_dir):
			logger.info("path: %s, target_dir: %s", path, target_dir)
			error = FILE_OP_ERROR_NONE
			free = getBookmarkSpaceInfo(MountCockpit.getInstance().getBookmark("MVC", target_dir))[2]
			size = self.getCountSize(path)[1]
			logger.debug("size: %s, free: %s", size, free)
			if free * 0.8 < size:
				logger.info("not enough space left: size: %s, free: %s", size, free)
				error = FILE_OP_ERROR_NO_DISKSPACE
			return error

		logger.info("file_op: %s, path: %s, target_dir: %s", file_op, path, target_dir)
		self.file_op_callback = file_op_callback
		error = FILE_OP_ERROR_NONE
		afile = self.source_selector.getFile("recordings", path)
		if afile:
			file_type = afile[FILE_IDX_TYPE]
			rel_path = afile[FILE_IDX_RELPATH]
			if file_op == FILE_OP_DELETE:
				afiles = self.sqlSelect("recordings", "rel_path = ?", [rel_path])
				for afile in afiles:
					path = afile[FILE_IDX_PATH]
					file_type = afile[FILE_IDX_TYPE]
					if "trashcan" in path:
						self.addJob(FILE_OP_DELETE, file_type, path, target_dir, file_op_callback)
					else:
						target_path = getMoveToTrashcanTarget(path)
						self.addJob(FILE_OP_MOVE, file_type, path, target_path, file_op_callback)
			elif file_op == FILE_OP_MOVE:
				if MountCockpit.getInstance().sameMountPoint("MVC", path, target_dir):
					afiles = self.sqlSelect("recordings", "rel_path = ?", [rel_path])
					logger.debug("afiles: %s", afiles)
					for afile in afiles:
						path = afile[FILE_IDX_PATH]
						target_path = getMoveTarget(path, target_dir)
						logger.debug("adding: %s > %s", path, target_path)

						self.addJob(file_op, file_type, path, target_path, file_op_callback)
				else:
					self.error = checkFreeSpace(path, target_dir)
					if not error:
						self.addJob(file_op, file_type, path, target_dir, file_op_callback)
					else:
						self.execFileOpCallback(file_op, path, target_dir, error)
			elif file_op == FILE_OP_COPY:
				self.error = checkFreeSpace(path, target_dir)
				if not error:
					self.addJob(file_op, file_type, path, target_dir, file_op_callback)
				else:
					self.execFileOpCallback(file_op, path, target_dir, error)
		else:
			if file_op == FILE_OP_DELETE:
				self.addJob(file_op, FILE_TYPE_FILE, path, target_dir, file_op_callback)

	def execFileOpCallback(self, file_op, path, target_dir, error):
		logger.info("file_op: %s, path: %s, target_dir: %s, error: %s", file_op, path, target_dir, error)
		if self.file_op_callback:
			self.file_op_callback(file_op, path, target_dir, FILE_OP_ERROR_NONE)

	def archive(self, archive_source_dir="", archive_target_dir="", callback=None):

		def isLink(path):
			if os.path.islink(path):
				return True
			if path != "/":
				return isLink(os.path.dirname(path))
			return False

		archive_files = 0
		if config.plugins.moviecockpit.archive_enable.value:
			if not archive_source_dir:
				archive_source_dir = config.plugins.moviecockpit.archive_source_dir.value
			if not archive_target_dir:
				archive_target_dir = config.plugins.moviecockpit.archive_target_dir.value
			logger.info("archive_source_dir: %s, archive_target_dir: %s", archive_source_dir, archive_target_dir)
			if os.path.exists(archive_source_dir) and os.path.exists(archive_target_dir):
				if os.path.realpath(archive_source_dir) != os.path.realpath(archive_target_dir):
					file_list = self.sqlSelect("recordings", "path LIKE ?", [archive_source_dir + "%"])
					for afile in file_list:
						logger.debug("afile: %s", afile)
						path = afile[FILE_IDX_PATH]
						if afile[FILE_IDX_TYPE] == FILE_TYPE_FILE and not isRecording(path) and "trashcan" not in path and not isLink(path):
							target_dir = getArchiveTarget(path, archive_target_dir)
							self.addJob(FILE_OP_MOVE, afile[FILE_IDX_TYPE], path, target_dir, callback)
							archive_files += 1
					if archive_files:
						self.addJob(FILE_OP_FSTRIM, None, "", "", None)
				else:
					logger.error("archive_source_dir and archive_target_dir are identical.")
			else:
				logger.error("archive_source_dir and/or archive_target_dir does not exist.")
		else:
			logger.debug("archive_enable is False")
		logger.info("archive_files: %s", archive_files)

	def purgeTrashcan(self, retention=0, callback=None):
		logger.info("retention: %s", retention)
		deleted_files = 0
		now = time()
		trashcan_dir = os.path.join(MountCockpit.getInstance().getHomeDir("MVC"), "trashcan")
		file_list = self.getMovieFileList(trashcan_dir, True, True)
		file_list += self.getMovieDirList(trashcan_dir, True)
		for afile in file_list:
			path = afile[FILE_IDX_PATH]
			file_type = afile[FILE_IDX_TYPE]
			st_mtime = 0
			if os.path.exists(path):
				st_mtime = os.stat(path).st_mtime
			if now > st_mtime + 24 * 60 * 60 * retention:
				logger.info("path: %s", path)
				deleted_files += 1
				self.addJob(FILE_OP_DELETE, file_type, path, None, callback)
		if deleted_files:
			self.addJob(FILE_OP_FSTRIM, None, "", "", None)
		logger.info("deleted_files: %d", deleted_files)

	def getMovieLockList(self):
		return self.source_selector.getLockList()

	def getMovieRecordings(self):
		return self.source_selector.getRecordings()

	def getMovieDirList(self, adir, top_level=False):
		return self.source_selector.getDirList(adir, top_level)

	def getMovieFileList(self, adir, top_level=False, recursive=False):
		return self.source_selector.getFileList(adir, top_level, recursive)

	def getMovieLogFileList(self, adir, top_level=False):
		return self.source_selector.getLogFileList(adir, top_level)

	def getMovieCountSize(self, path):
		return self.source_selector.getCountSize(path)

	def getMovieFile(self, table, path):
		logger.info("table: %s, path: %s", table, path)
		afile = self.source_selector.getFile(table, path)
		return afile
