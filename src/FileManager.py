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
from time import time
from Components.config import config
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from .Debug import logger
from .FileManagerUtils import FILE_TYPE_FILE, FILE_IDX_TYPE, FILE_IDX_PATH
from .FileManagerUtils import FILE_OP_DELETE, FILE_OP_MOVE
from .RecordingUtils import isRecording
from .FileManagerJob import FileManagerJob
from .SourceSelector import SourceSelector


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
		logger.info("file_op: %s, path: %s, target_dir: %s", file_op, path, target_dir)
		self.addJob(file_op, path, target_dir, file_op_callback)

	def archive(self, check=False, callback=None):
		logger.info("check: %s", check)
		archive_files = 0
		archive_source_dir = config.plugins.cachecockpit.archive_source_dir.value
		archive_target_dir = config.plugins.cachecockpit.archive_target_dir.value
		logger.info("archive_source_dir: %s, archive_target_dir: %s", archive_source_dir, archive_target_dir)
		if os.path.exists(archive_source_dir) and os.path.exists(archive_target_dir):
			if os.path.realpath(archive_source_dir) != os.path.realpath(archive_target_dir):
				file_list = self.sqlSelect("recordings", "path LIKE ?", [archive_source_dir + "%"])
				for afile in file_list:
					logger.debug("afile: %s", afile)
					if afile[FILE_IDX_TYPE] == FILE_TYPE_FILE and not isRecording(afile[FILE_IDX_PATH]) and "trashcan" not in afile[FILE_IDX_PATH]:
						if not check:
							logger.debug("path: %s", afile[FILE_IDX_PATH])
							source_dir = os.path.dirname(afile[FILE_IDX_PATH])
							source_sub_dir = source_dir[len(archive_source_dir) + 1:]
							target_dir = os.path.normpath(os.path.join(archive_target_dir, source_sub_dir))
							logger.debug("target_dir: %s", target_dir)
							self.addJob(FILE_OP_MOVE, afile[FILE_IDX_PATH], target_dir, callback)
						archive_files += 1
			else:
				logger.error("archive_source_dir and archive_target_dir are identical.")
		else:
			logger.error("archive_source_dir and/or archive_target_dir does not exist.")
		logger.debug("archive_files: %s", archive_files)
		return archive_files

	def purgeTrashcan(self, retention=0, callback=None):
		deleted_files = 0
		now = time()
		trashcan_dir = os.path.join(MountCockpit.getInstance().getHomeDir("MVC"), "trashcan")
		all_dirs = MountCockpit.getInstance().getVirtualDirs("MVC", [trashcan_dir])
		for adir in all_dirs:
			file_list = self.getFileList([adir], False)
			file_list += self.getDirList([adir])
			for afile in file_list:
				path = afile[FILE_IDX_PATH]
				if os.path.exists(path):
					if now > os.stat(path).st_mtime + 24 * 60 * 60 * retention:
						logger.info("path: %s", path)
						deleted_files += 1
						self.execFileOp(FILE_OP_DELETE, path, None, callback)
				else:
					logger.info("path: %s", path)
					deleted_files += 1
					self.execFileOp(FILE_OP_DELETE, path, None, callback)
		logger.info("deleted_files: %d", deleted_files)

	def getMovieLockList(self):
		return self.source_selector.getLockList()

	def getMovieRecordings(self):
		return self.source_selector.getRecordings()

	def getMovieDirList(self, dirs, top_level=False):
		return self.source_selector.getDirList(dirs, top_level)

	def getMovieFileList(self, dirs, top_level=False, recursively=False):
		return self.source_selector.getFileList(dirs, top_level, recursively)

	def getMovieLogFileList(self, dirs, top_level=False):
		return self.source_selector.getLogFileList(dirs, top_level)

	def getMovieCountSize(self, path):
		return self.source_selector.getCountSize(path)

	def getMovieFile(self, table, path):
		logger.info("table: %s, path: %s", table, path)
		afile = self.source_selector.getFile(table, path)
		return afile
