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
from Debug import logger
from pipes import quote
from MovieCoverUtils import getCoverPath, getCoverTargetDir
from Shell import Shell
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from Plugins.SystemPlugins.MountCockpit.MountUtils import getBookmarkSpaceInfo
from FileCache import FileCache
from Components.config import config
from FileOpUtils import FILE_OP_DELETE, FILE_OP_MOVE, FILE_OP_COPY, FILE_OP_ERROR_NONE, FILE_OP_ERROR_NO_DISKSPACE


class FileOp(Shell):

	def __init__(self):
		Shell.__init__(self)

	def abortFileOp(self):
		logger.info("...")
		self.abortShell()

	def execFileOp(self, file_op, path, target_dir, exec_file_op_callback=None):
		self.exec_file_op_callback = exec_file_op_callback
		error = FILE_OP_ERROR_NONE
		cmds = []
		callback = []
		logger.info("file_op: %s, path: %s, target_dir: %s", file_op, path, target_dir)
		if file_op == FILE_OP_DELETE:
			cmds = self.__execFileDelete(path)
			callback = [self.__deleteCallback, path, target_dir]
		elif file_op == FILE_OP_MOVE:
			free = size = 0
			if os.path.dirname(path) != target_dir and MountCockpit.getInstance().getMountPoint("MVC", path) != MountCockpit.getInstance().getMountPoint("MVC", target_dir):
				_used_percent, _used, free = getBookmarkSpaceInfo(target_dir)
				_count, size = FileCache.getInstance().getCountSize(path)
			logger.debug("FILE_OP_MOVE: size: %s, free: %s", size, free)
			if free * 0.8 >= size:
				callback = [self.__moveCallback, path, target_dir]
				cmds = self.__execFileMove(path, target_dir)
			else:
				logger.info("FILE_OP_MOVE: not enough space left: size: %s, free: %s", size, free)
				error = FILE_OP_ERROR_NO_DISKSPACE
		elif file_op == FILE_OP_COPY:
			free = size = 0
			if os.path.dirname(path) != target_dir:
				_used_percent, _used, free = getBookmarkSpaceInfo(target_dir)
				_count, size = FileCache.getInstance().getCountSize(path)
			logger.debug("FILE_OP_COPY: size: %s, free: %s", size, free)
			if free * 0.8 >= size:
				callback = [self.__copyCallback, path, target_dir]
				cmds = self.__execFileCopy(path, target_dir)
			else:
				logger.info("FILE_OP_MOVE: not enough space left: size: %s, free: %s", size, free)
				error = FILE_OP_ERROR_NO_DISKSPACE
		if cmds:
			logger.debug("cmds: %s", cmds)
			if file_op == FILE_OP_MOVE and MountCockpit.getInstance().getMountPoint("MVC", path) != MountCockpit.getInstance().getMountPoint("MVC", target_dir)\
				or file_op == FILE_OP_COPY and os.path.dirname(path) != target_dir:
				# wait for cmds execution
				self.executeShell((cmds, callback))
			else:
				# don't wait for cmds execution
				self.executeShell((cmds, None))
				if callback:
					function = callback[0]
					args = callback[1:]
					logger.debug("function: %s, args: %s", function, args)
					function(*args)
		else:
			if self.exec_file_op_callback:
				self.exec_file_op_callback(file_op, path, target_dir, error)

	def __deleteCallback(self, path, target_dir):
		logger.info("path: %s, target_dir: %s", path, target_dir)
		FileCache.getInstance().delete(path)
		if self.exec_file_op_callback:
			self.exec_file_op_callback(FILE_OP_DELETE, path, target_dir, FILE_OP_ERROR_NONE)

	def __moveCallback(self, path, target_dir):
		logger.info("path: %s, target_dir: %s", path, target_dir)
		FileCache.getInstance().move(path, target_dir)
		if "trashcan" in target_dir and not FileCache.getInstance().exists(target_dir):
			FileCache.getInstance().loadDatabaseFile(target_dir)
		if self.exec_file_op_callback:
			self.exec_file_op_callback(FILE_OP_MOVE, path, target_dir, FILE_OP_ERROR_NONE)

	def __copyCallback(self, path, target_dir):
		logger.info("path: %s, target_dir: %s", path, target_dir)
		FileCache.getInstance().copy(path, target_dir)
		if self.exec_file_op_callback:
			self.exec_file_op_callback(FILE_OP_COPY, path, target_dir, FILE_OP_ERROR_NONE)

	def __execFileDelete(self, path):
		logger.info("path: %s", path)
		cmds = []
		if os.path.isfile(path):
			cover_path, backdrop_path, info_path = getCoverPath(path)
			cmds.append("rm -f " + quote(cover_path))
			cmds.append("rm -f " + quote(backdrop_path))
			cmds.append("rm -f " + quote(info_path))
			path = os.path.splitext(path)[0]
			cmds.append("rm -f " + quote(path) + ".*")
		elif os.path.isdir(path):
			cmds.append("rm -rf " + quote(path))
			cover_target_dir, _backdrop_target_dir, _info_target_dir = getCoverTargetDir(path)
			cmds.append("rm -rf " + quote(cover_target_dir))
		elif os.path.islink(path):
			cmds.append("rm -f " + quote(path))
			cover_target_dir, _backdrop_target_dir, _info_target_dir = getCoverTargetDir(path)
			cmds.append("rm -f " + quote(cover_target_dir))
		logger.debug("cmds: %s", cmds)
		return cmds

	def __execFileMove(self, path, target_dir):
		logger.info("path: %s, target_dir: %s", path, target_dir)
		cmds = self.__changeFileOwner(path, target_dir)
		if os.path.isfile(path):
			cmds += self.__execCoverOp("mv", path, target_dir)
			path = os.path.splitext(path)[0]
			if "trashcan" in target_dir:
				cmds.append("touch " + quote(path) + ".*")
			cmds.append("mv " + quote(path) + ".*" + " " + quote(target_dir))
		elif os.path.isdir(path) or os.path.islink(path):
			if "trashcan" in target_dir:
				cmds.append("touch " + quote(path))
			cmds.append("mv " + quote(path) + " " + quote(target_dir))
		logger.debug("cmds: %s", cmds)
		return cmds

	def __execFileCopy(self, path, target_dir):
		logger.info("path: %s, target_dir: %s", path, target_dir)
		cmds = self.__changeFileOwner(path, target_dir)
		if os.path.isfile(path):
			cmds += self.__execCoverOp("cp", path, target_dir)
			path = os.path.splitext(path)[0]
			cmds.append("cp " + quote(path) + ".* " + quote(target_dir))
		elif os.path.isdir(path) or os.path.islink(path):
			cmds.append("cp -a " + quote(path) + " " + quote(target_dir))
		logger.debug("cmds: %s", cmds)
		return cmds

	def __execCoverOp(self, op, path, target_dir):
		logger.info("op: %s, path: %s, target_dir: %s", op, path, target_dir)
		cmds = []
		cover_path, backdrop_path, info_path = getCoverPath(path)
		cover_target_dir, backdrop_target_dir, info_target_dir = getCoverTargetDir(target_dir)

		logger.debug("cover_path: %s, cover_target_dir: %s", cover_path, cover_target_dir)
		logger.debug("backdrop_path: %s, backdrop_target_dir: %s", backdrop_path, backdrop_target_dir)
		logger.debug("info_path: %s, info_target_dir: %s", info_path, info_target_dir)

		for adir in [target_dir, cover_target_dir, backdrop_target_dir, info_target_dir]:
			if not os.path.isdir(adir):
				cmds.append("mkdir -p " + quote(adir))

		if "trashcan" in target_dir:
			trashcan_dir = target_dir
			if config.plugins.moviecockpit.cover_flash.value:
				bookmark = MountCockpit.getInstance().getBookmark("MVC", target_dir)
				trashcan_dir = os.path.normpath(config.plugins.moviecockpit.cover_bookmark.value + "/" + bookmark + "/trashcan")
			if not os.path.isdir(trashcan_dir):
				cmds.append("mkdir -p " + quote(trashcan_dir))
			cover_target_dir = trashcan_dir
			backdrop_target_dir = trashcan_dir
			info_target_dir = trashcan_dir

		cmds.append(op + " " + quote(cover_path) + " " + quote(cover_target_dir))
		cmds.append(op + " " + quote(backdrop_path) + " " + quote(backdrop_target_dir))
		cmds.append(op + " " + quote(info_path) + " " + quote(info_target_dir))

		logger.debug("cmds: %s", cmds)
		return cmds

	def __changeFileOwner(self, path, target_dir):
		cmds = []
		if MountCockpit.getInstance().getMountPoint("MVC", target_dir) != MountCockpit.getInstance().getMountPoint("MVC", path):
			# need to change file ownership to match target filesystem file creation
			tfile = quote(target_dir + "/owner_test")
			sfile = quote(path) + ".*"
			cmds.append("touch %s;ls -l %s | while read flags i owner group crap;do chown $owner:$group %s;done;rm %s" % (tfile, tfile, sfile, tfile))
		return cmds
