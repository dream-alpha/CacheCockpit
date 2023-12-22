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


from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from Plugins.SystemPlugins.MountCockpit.MountUtils import getBookmarkSpaceInfo
from .Debug import logger
from .FileManagerUtils import FILE_OP_DELETE, FILE_OP_MOVE, FILE_OP_COPY, FILE_OP_FSTRIM
from .FileManagerUtils import FILE_OP_ERROR_NONE, FILE_OP_ERROR_NO_DISKSPACE
from .FileOp import FileOp
from .FileManagerCache import FileManagerCache


class FileCache(FileOp, FileManagerCache):

	def __init__(self):
		FileOp.__init__(self)
		FileManagerCache.__init__(self)

	def execCacheOpCallback(self, _file_op, _path, _target_dir, _error):
		logger.error("should be overridden in child class")

	def execCacheOp(self, file_op, _file_type, path, target_dir):

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
		self.file_op = file_op
		self.path = path
		self.target_dir = target_dir
		self.error = FILE_OP_ERROR_NONE

		if self.file_op == FILE_OP_DELETE:
			self.execFileOp(self.file_op, self.file_type, self.path, self.target_dir)
		elif self.file_op == FILE_OP_MOVE:
			if not MountCockpit.getInstance().sameMountPoint("MVC", self.path, self.target_dir):
				self.error = checkFreeSpace(self.path, self.target_dir)
				if not self.error:
					self.execFileOp(self.file_op, self.file_type, self.path, self.target_dir)
				else:
					self.execFileOpCallback(self.file_op, self.path, self.target_dir, self.error)
			else:
				self.execFileOp(self.file_op, self.file_type, self.path, self.target_dir)
		elif self.file_op == FILE_OP_COPY:
			self.error = checkFreeSpace(self.path, self.target_dir)
			if not self.error:
				self.execFileOp(self.file_op, self.file_type, self.path, self.target_dir)
			else:
				self.execFileOpCallback(self.file_op, self.path, self.target_dir, self.error)
		elif self.file_op == FILE_OP_FSTRIM:
			self.execFileOp(self.file_op, self.file_type, "", "")

	def execFileOpCallback(self, file_op, path, target_dir, error):
		logger.info("error: %s", error)
		if not error:
			self.execCacheFileOp(file_op, path, target_dir)
		self.execCacheOpCallback(file_op, path, target_dir, error)
