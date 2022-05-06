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
from __init__ import _
from Debug import logger
from enigma import eTimer
from Components.Task import Task
from FileOp import FileOp
from FileManagerCache import FileManagerCache
from FileManagerUtils import FILE_OP_MOVE, FILE_OP_COPY, FILE_OP_DELETE, FILE_OP_ERROR_NONE, FILE_OP_ERROR_ABORT, FILE_OP_ERROR_NO_DISKSPACE
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from Plugins.SystemPlugins.MountCockpit.MountUtils import getBookmarkSpaceInfo


ACTIVITY_TIMER_DELAY = 1000
file_ops = {FILE_OP_DELETE: _("Deleting"), FILE_OP_MOVE: _("Moving"), FILE_OP_COPY: _("Copying")}


class FileManagerTask(Task, FileManagerCache, FileOp):

	def __init__(self, job, file_op, path, target_dir, job_callback, file_op_callback):
		logger.info("file_op = %s, path = %s, target_dir = %s", file_op, path, target_dir)
		Task.__init__(self, job, _("File task") + ": " + file_ops[file_op])
		FileManagerCache.__init__(self)
		FileOp.__init__(self)
		self.job = job
		self.file_op = file_op
		self.path = path
		self.target_dir = target_dir
		self.file_op_callback = file_op_callback
		self.job_callback = job_callback
		self.activity_timer = eTimer()
		self.activity_timer_conn = self.activity_timer.timeout.connect(self.updateProgress)

	def abort(self):
		logger.debug("path: %s", self.path)
		self.abortFileOp()
		self.error = FILE_OP_ERROR_ABORT

	def run(self, callback):

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

		logger.info("self.file_op: %s, self.path: %s, self.target_dir: %s, callback: %s", self.file_op, self.path, self.target_dir, callback)
		self.callback = callback
		self.error = FILE_OP_ERROR_NONE
		self.activity_timer.start(ACTIVITY_TIMER_DELAY)
		self.source_size = 0
		if os.path.exists(self.path):
			self.source_size = os.path.getsize(self.path)
		self.updateProgress()

		if self.file_op == FILE_OP_DELETE:
			self.execFileOp(self.file_op, self.path, self.target_dir, self.execFileOpCallback)
		elif self.file_op == FILE_OP_MOVE:
			if not MountCockpit.getInstance().sameMountPoint("MVC", self.path, self.target_dir):
				self.error = checkFreeSpace(self.path, self.target_dir)
				if not self.error:
					self.execFileOp(self.file_op, self.path, self.target_dir, self.execFileOpCallback)
				else:
					self.execFileOpCallback(self.file_op, self.path, self.target_dir, self.error)
			else:
				self.execFileOp(self.file_op, self.path, self.target_dir, self.execFileOpCallback)
		elif self.file_op == FILE_OP_COPY:
			self.error = checkFreeSpace(self.path, self.target_dir)
			if not self.error:
				self.execFileOp(self.file_op, self.path, self.target_dir, self.execFileOpCallback)
			else:
				self.execFileOpCallback(self.file_op, self.path, self.target_dir, self.error)

	def execFileOpCallback(self, _file_op, _path, _target_dir, _error):
		logger.info("...")
		self.activity_timer.stop()
		self.finish()

	def updateProgress(self):
		source_file_name = os.path.basename(self.path)
		target_size = 0
		if self.target_dir:
			target_file = os.path.join(self.target_dir, source_file_name)
			if os.path.exists(target_file):
				target_size = os.path.getsize(target_file)
		logger.debug("source_size: %d, target_size: %d", self.source_size, target_size)
		progress = int(float(target_size) / float(self.source_size) * 100) if self.source_size else 100
		logger.debug("path: %s, target_dir: %s, progress: %d", self.path, self.target_dir, progress)
		self.setProgress(progress)

	def afterRun(self):
		logger.info("self.file_op: %s, self.path: %s, self.target_dir: %s", self.file_op, self.path, self.target_dir)
		logger.info("self.job_callback: %s", self.job_callback)
		if self.job_callback:
			self.job_callback(self.file_op, self.path, self.target_dir, self.error, self.file_op_callback)
