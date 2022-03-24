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
from FileCache import FileCache
from Components.Task import Job, job_manager
from FileOpManagerTask import FileOpManagerTask
from FileOpUtils import FILE_OP_DELETE


class FileOpManagerJob():

	def __init__(self):
		return

	def getLockList(self):
		lock_list = {}
		jobs = self.getPendingJobs()
		for job in jobs:
			lock_list[job.name] = job.file_op
		logger.debug("lock_list: %s", lock_list)
		return lock_list

	def addJob(self, file_op, path, target_dir, fileop_callback):
		job = Job(path)
		job.file_op = file_op
		jobs = job_manager.getPendingJobs()
		add = True
		for ajob in jobs:
			if ajob.name == job.name:
				add = False
				break
		if add:
			FileOpManagerTask(job, file_op, path, target_dir, self.callbackJob, fileop_callback)
			job_manager.AddJob(job)

	def callbackJob(self, file_op, path, target_dir, error, fileop_callback):
		logger.debug("path: %s, error: %s, fileop_callback: %s", path, error, fileop_callback)
		if error:
			job_manager.active_jobs = []
		else:
			FileCache.getInstance().execFileOp(file_op, path, target_dir)
		if fileop_callback:
			try:
				fileop_callback(file_op, path, target_dir, error)
			except Exception as e:
				logger.info("fileop_callback: %s, exception: %s", fileop_callback, e)

	def cancelJobs(self):
		logger.debug("...")
		job_manager.active_jobs = []
		if job_manager.active_job:
			job_manager.active_job.abort()

	def getPendingJobs(self):
		return job_manager.getPendingJobs()

	def getProgress(self):
		file_name = ""
		file_op = FILE_OP_DELETE
		jobs = self.getPendingJobs()
		progress = 0
		if jobs:
			job = jobs[0]
			file_name = os.path.basename(job.name)
			file_op = job.file_op
			progress = job.progress
		return len(jobs), file_name, file_op, progress
