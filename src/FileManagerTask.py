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


import os
from Components.Task import Task
from enigma import eTimer
from .Debug import logger
from .FileManagerUtils import FILE_OP_ERROR_NONE, FILE_TASK, file_op_msg
from .CacheOps import CacheOps
from .CacheLoad import CacheLoad
from .DiskOps import DiskOps


ACTIVITY_TIMER_DELAY = 1000


class FileManagerTask(Task, DiskOps, CacheLoad, CacheOps):

    def __init__(self, job, file_op, file_type, path, target_dir, job_callback):
        logger.info("file_op = %s, path = %s, target_dir = %s",
                    file_op, path, target_dir)
        Task.__init__(self, job, FILE_TASK + ": " + file_op_msg[file_op])
        self.plugin = job.plugin
        CacheLoad.__init__(self, self.plugin)
        CacheOps.__init__(self)
        DiskOps.__init__(self)
        self.job = job
        self.file_op = file_op
        self.file_type = file_type
        self.path = path
        self.target_dir = target_dir
        self.target_path = os.path.join(
            self.target_dir, os.path.basename(path)) if target_dir else ""
        self.job_callback = job_callback
        self.error = FILE_OP_ERROR_NONE
        self.activity_timer = eTimer()
        self.activity_timer_conn = self.activity_timer.timeout.connect(
            self.updateProgress)

    def abort(self, *_args):
        logger.debug("path: %s", self.path)
        self.abortFileOp()

    def run(self, callback):
        logger.info("self.file_op: %s, self.path: %s, self.target_dir: %s, callback: %s",
                    self.file_op, self.path, self.target_dir, callback)
        self.callback = callback
        self.activity_timer.start(ACTIVITY_TIMER_DELAY)
        self.source_size = 0
        self.setProgress(0)
        self.execDiskOp(self.file_op, self.file_type,
                        self.path, self.target_dir)

    def execDiskOpCallback(self, file_op, path, target_dir, error):
        logger.info("file_op: %s, path: %s, target_dir: %s, error: %s",
                    file_op, path, target_dir, error)
        self.error = error
        self.activity_timer.stop()
        if error == FILE_OP_ERROR_NONE:
            self.execCacheOp(file_op, path, target_dir)
        self.finish()

    def updateProgress(self):
        if self.source_size == 0:
            if os.path.exists(self.path):
                self.source_size = os.path.getsize(self.path)
        target_size = 0
        if self.target_path:
            if os.path.exists(self.target_path):
                target_size = os.path.getsize(self.target_path)
        logger.debug("source_size: %d, target_size: %d",
                     self.source_size, target_size)
        progress = int(float(target_size) / float(self.source_size)
                       * 100) if self.source_size else 100
        logger.debug("path: %s, target_dir: %s, progress: %d",
                     self.path, self.target_dir, progress)
        self.setProgress(progress)

    def afterRun(self):
        logger.info("self.file_op: %s, self.path: %s, self.target_dir: %s",
                    self.file_op, self.path, self.target_dir)
        logger.info("self.job_callback: %s", self.job_callback)
        if self.job_callback:
            self.job_callback(self.job, self.file_op,
                              self.path, self.target_dir, self.error)
