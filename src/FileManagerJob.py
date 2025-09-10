#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2025 by dream-alpha
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


from Components.Task import Job
from Plugins.SystemPlugins.JobCockpit.JobSupervisor import JobSupervisor
from .FileManagerTask import FileManagerTask
from .FileManagerUtils import FILE_OP_NONE, FILE_OP_FSTRIM, FILE_IDX_NAME
from .DelayTimer import DelayTimer
from .JobUtils import getPendingJobs
from .Debug import logger


class FileManagerJob():

    def __init__(self):
        self.job_manager = JobSupervisor.getInstance().getJobManager("MVC")

    def getLockList(self):
        lock_list = {}
        jobs = getPendingJobs("MVC")
        for job in jobs:
            lock_list[job.name] = job.file_op
        logger.debug("lock_list: %s", lock_list)
        return lock_list

    def addJob(self, file_op, file_type, path, target_dir, file_op_callback):
        logger.info("file_op: %s, path: %s, target_dir: %s, file_op_callback: %s",
                    file_op, path, target_dir, file_op_callback)
        job = Job(path)
        job.file_op = file_op
        job.file_op_callback = file_op_callback
        job.plugin = self.plugin
        FileManagerTask(job, file_op, file_type, path,
                        target_dir, self.callbackJob)
        self.job_manager.AddJob(job)

    def callbackJob(self, job, file_op, path, target_dir, error):
        logger.info("file_op: %s, path: %s, target_dir: %s, error: %s",
                    file_op, path, target_dir, error)
        file_op_callback = job.file_op_callback
        if error:
            self.job_manager.active_jobs = []
        if file_op_callback:
            try:
                logger.info("calling file_op_callback")
                DelayTimer(100, file_op_callback, file_op,
                           path, target_dir, error)
            except Exception as e:
                logger.info("file_op_callback: %s, exception: %s",
                            file_op_callback, e)

    def cancelJobs(self):
        logger.info("...")
        self.job_manager.active_jobs = []
        if self.job_manager.active_job:
            self.job_manager.active_job.abort()

    def getJobsProgress(self):
        file_name = ""
        file_op = FILE_OP_NONE
        jobs = getPendingJobs("MVC")
        progress = 0
        files = 0
        for ajob in jobs:
            if ajob.file_op != FILE_OP_FSTRIM:
                files += 1
        if files:
            ajob = jobs[0]
            afile = self.getFile("table1", ajob.name)
            file_name = afile[FILE_IDX_NAME] if afile else ""
            file_op = ajob.file_op
            progress = ajob.progress
        return files, file_name, file_op, progress
