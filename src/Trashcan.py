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
from Components.config import config
from DelayTimer import DelayTimer
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from FileCacheUtils import FILE_IDX_PATH, FILE_IDX_TYPE
from FileCache import FileCache
from FileOp import FileOp
from FileOpUtils import FILE_OP_DELETE


instance = None


class Trashcan(FileOp):

	def __init__(self):
		FileOp.__init__(self)
		self.__schedulePurge()

	@staticmethod
	def getInstance():
		global instance
		if instance is None:
			instance = Trashcan()
		return instance

	def __schedulePurge(self):
		if config.plugins.cachecockpit.trashcan_enable.value and config.plugins.cachecockpit.trashcan_clean.value:
			seconds = 24 * 60 * 60
			DelayTimer(1000 * seconds, self.__schedulePurge)
			DelayTimer(10000, self.purgeTrashcan)
			logger.info("next trashcan cleanup in %s minutes", seconds / 60)

	def purgeTrashcan(self):
		logger.info("...")
		deleted_files = 0
		now = time.localtime()
		trashcan_dir = os.path.join(MountCockpit.getInstance().getHomeDir("MVC"), "trashcan")
		logger.debug("trashcan_dir: %s", trashcan_dir)
		file_list = FileCache.getInstance().getFileList([trashcan_dir])
		file_list += FileCache.getInstance().getDirList([trashcan_dir])
		for afile in file_list:
			path = afile[FILE_IDX_PATH]
			file_type = afile[FILE_IDX_TYPE]
			if os.path.exists(path):
				if now > time.localtime(os.stat(path).st_mtime + 24 * 60 * 60 * int(config.plugins.cachecockpit.trashcan_retention.value)):
					logger.info("path: %s", path)
					deleted_files += 1
					self.execFileOp(FILE_OP_DELETE, path, None, file_type)
			else:
				logger.info("path: %s", path)
				deleted_files += 1
				self.execFileOp(FILE_OP_DELETE, path, None, file_type)
		logger.info("deleted_files: %d", deleted_files)
