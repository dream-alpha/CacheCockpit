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
from Components.Task import Task
from enigma import eTimer
from .Debug import logger
from .FileManagerUtils import FILE_OP_ERROR_NONE, FILE_OP_ERROR_ABORT, FILE_TASK, file_op_msg
from .FileManagerUtils import FILE_OP_DELETE, FILE_OP_FSTRIM
from .FileManagerCache import FileManagerCache
from .FileManagerDisk import FileManagerDisk
from .DelayTimer import DelayTimer


ACTIVITY_TIMER_DELAY = 1000


class FileManagerTask(Task, FileManagerDisk, FileManagerCache):

	def __init__(self, job, file_op, file_type, path, target_dir, job_callback, file_op_callback):
		logger.info("file_op = %s, path = %s, target_dir = %s", file_op, path, target_dir)
		Task.__init__(self, job, FILE_TASK + ": " + file_op_msg[file_op])
		FileManagerCache.__init__(self)
		FileManagerDisk.__init__(self)
		self.job = job
		self.file_op = file_op
		self.file_type = file_type
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
		logger.info("self.file_op: %s, self.path: %s, self.target_dir: %s, callback: %s", self.file_op, self.path, self.target_dir, callback)
		self.callback = callback
		self.error = FILE_OP_ERROR_NONE
		self.activity_timer.start(ACTIVITY_TIMER_DELAY)
		self.source_size = 0
		if os.path.exists(self.path):
			if self.file_op != FILE_OP_FSTRIM:
				self.source_size = os.path.getsize(self.path)
				self.updateProgress()
				self.execDiskOp(self.file_op, self.file_type, self.path, self.target_dir)
		else:
			if self.file_op == FILE_OP_DELETE:
				DelayTimer(50, self.execDiskOpCallback, self.file_op, self.path, self.target_dir, FILE_OP_ERROR_NONE)
			elif self.file_op == FILE_OP_FSTRIM:
				self.execDiskOp(self.file_op, self.file_type, self.path, self.target_dir)

	def execDiskOpCallback(self, file_op, path, target_dir, error):
		if not error:
			self.execCacheOp(file_op, path, target_dir)
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
