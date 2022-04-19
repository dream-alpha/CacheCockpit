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
from MovieCoverUtils import getCoverPath
from Shell import Shell
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from FileManagerUtils import FILE_OP_DELETE, FILE_OP_MOVE, FILE_OP_COPY, FILE_OP_ERROR_NONE
from ServiceUtils import ALL_VIDEO


class FileOp(Shell):

	def __init__(self):
		Shell.__init__(self)

	def abortFileOp(self):
		logger.info("...")
		self.abortShell()

	def execFileOp(self, file_op, path, target_dir, exec_file_op_callback=None):
		self.exec_file_op_callback = exec_file_op_callback
		error = FILE_OP_ERROR_NONE
		cmds = [[], [], []] # first execution script, second execution script, abort cleanup script
		wait_for_completion = True
		logger.info("file_op: %s, path: %s, target_dir: %s, exec_file_op_callback: %s", file_op, path, target_dir, exec_file_op_callback)
		if file_op == FILE_OP_DELETE:
			cmds[0] = self.__execFileDelete(path, delete_cover=True)
		elif file_op == FILE_OP_MOVE:
			if MountCockpit.getInstance().sameMountPoint("MVC", path, target_dir):
				cmds[0] = self.__execFileMove(path, target_dir)
				wait_for_completion = False
			else:
				cmds[0] = self.__execFileCopy(path, target_dir)
				cmds[1] = self.__execFileDelete(path, delete_cover=False)
				cmds[2] = self.__execFileDelete(os.path.join(target_dir, os.path.basename(path)), force=True)
		elif file_op == FILE_OP_COPY:
			cmds[0] = self.__execFileCopy(path, target_dir)
			cmds[2] = self.__execFileDelete(os.path.join(target_dir, os.path.basename(path)), force=True)
		logger.info("wait_for_completion: %s, cmds: %s", wait_for_completion, cmds)
		if cmds:
			if wait_for_completion:
				self.executeShell(cmds, self.exec_file_op_callback, file_op, path, target_dir, error)
			else:
				self.executeShell(cmds, None, file_op, path, target_dir, error)
				self.exec_file_op_callback(file_op, path, target_dir, error)
		else:
			self.exec_file_op_callback(file_op, path, target_dir, error)

	def __execFileDelete(self, path, delete_cover=False, force=False):
		logger.info("path: %s, delete_cover: %s, forc: %s", path, delete_cover, force)
		cmds = []
		if force:
			cmds.append("rm -f %s.*" % quote(os.path.splitext(path)[0]))
		else:
			if os.path.isfile(path):
				if delete_cover:
					cmds.append("rm -f %s.*" % quote(os.path.splitext(getCoverPath(path)[0])[0]))
				cmds.append("rm -f %s.*" % quote(os.path.splitext(path)[0]))
			elif os.path.isdir(path):
				if delete_cover:
					for root, _dirs, files in os.walk(path):
						for file in files:
							fname = os.path.join(root, file)
							if os.path.splitext(fname)[1] in ALL_VIDEO:
								cmds.append("rm -f %s.*" % quote(os.path.splitext(getCoverPath(fname)[0])[0]))
				cmds.append("rm -rf %s" % quote(path))
			elif os.path.islink(path):
				cmds.append("rm -f %s" % quote(path))
		logger.info("cmds: %s", cmds)
		return cmds

	def __execFileMove(self, path, target_dir):
		logger.info("path: %s, target_dir: %s", path, target_dir)
		cmds = self.__changeFileOwner(path, target_dir)
		if os.path.isfile(path):
			if "trashcan" in target_dir:
				cmds.append("touch %s.*" % quote(os.path.splitext(path)[0]))
			cmds.append("mkdir -p %s" % quote(target_dir))
			cmds.append("mv %s.* %s" % (quote(os.path.splitext(path)[0]), quote(target_dir)))
		elif os.path.isdir(path):
			if "trashcan" in target_dir:
				cmds.append("touch %s" % quote(path))
			cmds.append("mkdir -p %s" % quote(target_dir))
			cmds.append("mv %s %s" % (quote(path), quote(target_dir)))
		elif os.path.islink(path):
			cmds.append("mv %s %s" % (quote(path), quote(target_dir)))
		logger.info("cmds: %s", cmds)
		return cmds

	def __execFileCopy(self, path, target_dir):
		logger.info("path: %s, target_dir: %s", path, target_dir)
		cmds = self.__changeFileOwner(path, target_dir)
		if os.path.isfile(path):
			cmds.append("mkdir -p %s" % quote(target_dir))
			cmds.append("cp -dp %s.* %s" % (quote(os.path.splitext(path)[0]), quote(target_dir)))
		elif os.path.isdir(path):
			cmds.append("mkdir -p %s" % quote(target_dir))
			cmds.append("cp -a %s %s" % (quote(path), quote(target_dir)))
		elif os.path.islink(path):
			cmds.append("cp -dp %s %s" % (quote(path), quote(target_dir)))
		logger.info("cmds: %s", cmds)
		return cmds

	def __changeFileOwner(self, path, target_dir):
		cmds = []
		if MountCockpit.getInstance().getMountPoint("MVC", target_dir) != MountCockpit.getInstance().getMountPoint("MVC", path):
			# need to change file ownership to match target filesystem file creation
			tfile = quote(target_dir + "/owner_test")
			sfile = quote(path) + ".*"
			cmds.append("touch %s;ls -l %s | while read flags i owner group crap;do chown $owner:$group %s;done;rm %s" % (tfile, tfile, sfile, tfile))
		logger.info("cmds: %s", cmds)
		return cmds
