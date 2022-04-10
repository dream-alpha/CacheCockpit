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
from FileManagerUtils import FILE_TYPE_FILE, FILE_TYPE_DIR, FILE_IDX_TYPE, FILE_IDX_PATH, FILE_OP_ERROR
from RecordingUtils import isRecording
from FileManagerUtils import FILE_OP_DELETE, FILE_OP_MOVE
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from FileManagerJob import FileManagerJob


instance = None


class FileManager(FileManagerJob):

	def __init__(self):
		FileManagerJob.__init__(self)

	@staticmethod
	def getInstance():
		global instance
		if instance is None:
			instance = FileManager()
		return instance

	def execFileManagerOp(self, file_op, path, target_dir=None, file_op_callback=None):
		logger.info("file_op: %s, path: %s, target_dir: %s", file_op, path, target_dir)
		afile = self.getFile(path)
		if afile:
			self.addJob(file_op, path, target_dir, file_op_callback)
		else:
			try:
				error = FILE_OP_ERROR
				if file_op_callback:
					file_op_callback(file_op, path, target_dir, error)
			except Exception as e:
				logger.error("exception: %s", e)

	def archive(self, callback=None):

		def addDirectory(adir):
			logger.info("adir: %s", adir)
			file_list = self.getFileList([adir])
			file_list += self.getDirList([adir])
			for afile in file_list:
				if afile[FILE_IDX_TYPE] == FILE_TYPE_FILE and not isRecording(afile[FILE_IDX_PATH]):
					logger.debug("path: %s", afile[FILE_IDX_PATH])
					source_dir = os.path.dirname(afile[FILE_IDX_PATH])
					source_sub_dir = source_dir[len(archive_source_dir) + 1:]
					target_dir = os.path.normpath(os.path.join(archive_target_dir, source_sub_dir))
					logger.debug("target_dir: %s", target_dir)
					self.addJob(FILE_OP_MOVE, afile[FILE_IDX_PATH], target_dir, callback)
				elif afile[FILE_IDX_TYPE] == FILE_TYPE_DIR:
					addDirectory(afile[FILE_IDX_PATH])

		logger.info("...")
		archive_source_dir = config.plugins.cachecockpit.archive_source_dir.value
		archive_target_dir = config.plugins.cachecockpit.archive_target_dir.value
		logger.info("archive_source_dir: %s, archive_target_dir: %s", archive_source_dir, archive_target_dir)
		if os.path.exists(archive_source_dir) and os.path.exists(archive_target_dir):
			if os.path.realpath(archive_source_dir) != os.path.realpath(archive_target_dir):
				addDirectory(archive_source_dir)
			else:
				logger.error("archive_source_dir and archive_target_dir are identical.")
		else:
			logger.error("archive_source_dir and/or archive_target_dir does not exist.")

	def purgeTrashcan(self, retention=0):
		logger.info("...")
		deleted_files = 0
		now = time.localtime()
		trashcan_dir = os.path.join(MountCockpit.getInstance().getHomeDir("MVC"), "trashcan")
		logger.debug("trashcan_dir: %s", trashcan_dir)
		file_list = self.getFileList([trashcan_dir])
		file_list += self.getDirList([trashcan_dir])
		for afile in file_list:
			path = afile[FILE_IDX_PATH]
			if os.path.exists(path):
				if now > time.localtime(os.stat(path).st_mtime + 24 * 60 * 60 * retention):
					logger.info("path: %s", path)
					deleted_files += 1
					self.execFileManagerOp(FILE_OP_DELETE, path)
			else:
				logger.info("path: %s", path)
				deleted_files += 1
				self.execFileManagerOp(FILE_OP_DELETE, path)
		logger.info("deleted_files: %d", deleted_files)
