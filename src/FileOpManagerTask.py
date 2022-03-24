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
from FileOpUtils import FILE_OP_MOVE, FILE_OP_COPY, FILE_OP_DELETE, FILE_OP_ERROR_NONE, FILE_OP_ERROR_ABORT


ACTIVITY_TIMER_DELAY = 1000
file_ops = {FILE_OP_DELETE: _("Deleting"), FILE_OP_MOVE: _("Moving"), FILE_OP_COPY: _("Copying")}


class FileOpManagerTask(Task):

	def __init__(self, job, file_op, path, target_dir, job_callback, fileop_callback):
		logger.info("file_op = %s, path = %s, target_dir = %s", file_op, path, target_dir)
		Task.__init__(self, job, _("File task") + ": " + file_ops[file_op])
		self.job = job
		self.file_op = file_op
		self.path = path
		self.target_dir = target_dir
		self.fileop_callback = fileop_callback
		self.job_callback = job_callback
		self.source_size = 0
		self.error = FILE_OP_ERROR_NONE
		self.activity_timer = eTimer()
		self.activity_timer_conn = self.activity_timer.timeout.connect(self.updateProgress)

	def abort(self):
		logger.debug("path: %s", self.path)
		self.error = FILE_OP_ERROR_ABORT
		FileOp.getInstance().abortFileOp()
		if os.path.exists(self.path):
			target_path = os.path.join(self.target_dir, os.path.basename(self.path))
			FileOp.getInstance().execFileOp(FILE_OP_DELETE, target_path, None, None)
		self.activity_timer.stop()
		self.finish()

	def run(self, callback):
		logger.debug("callback: %s", callback)
		self.callback = callback
		self.error = FILE_OP_ERROR_NONE
		logger.debug("self.callback: %s", self.callback)
		FileOp.getInstance().execFileOp(self.file_op, self.path, self.target_dir, self.execFileOpCallback)
		self.source_size = os.path.getsize(self.path)
		self.activity_timer.start(ACTIVITY_TIMER_DELAY)
		self.updateProgress()

	def execFileOpCallback(self, _file_op, path, target_dir, error):
		logger.debug("file_op: %s, path: %s, target_dir: %s, error: %s", _file_op, path, target_dir, error)
		self.error = error
		self.activity_timer.stop()
		self.finish()

	def updateProgress(self):
		source_file_name = os.path.basename(self.path)
		target_size = 0
		target_file = os.path.join(self.target_dir, source_file_name)
		if os.path.exists(target_file):
			target_size = os.path.getsize(target_file)
		logger.debug("source_size: %d, target_size: %d", self.source_size, target_size)
		progress = int(float(target_size) / float(self.source_size) * 100) if self.source_size else 100
		logger.debug("path: %s, target_dir: %s, progress: %d", self.path, self.target_dir, progress)
		self.setProgress(progress)

	def afterRun(self):
		logger.debug("path: %s", self.path)
		if self.job_callback:
			self.job_callback(self.file_op, self.path, self.target_dir, self.error, self.fileop_callback)
