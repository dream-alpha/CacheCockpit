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


from pipes import quote
from enigma import eConsoleAppContainer
from .Debug import logger
from .DelayTimer import DelayTimer
from .FileManagerUtils import FILE_OP_ERROR_ABORT


class Shell():

    def __init__(self):
        logger.info("...")
        self.container1 = eConsoleAppContainer()
        self.container1_appClosed_conn = self.container1.appClosed.connect(
            self.finished1)
        self.container2 = eConsoleAppContainer()
        self.container2_appClosed_conn = self.container2.appClosed.connect(
            self.finished2)

    def execDiskOpCallback(self, *__):
        logger.error("should be overridden in child class")

    def execShell(self, scripts, wait_for_completion, *args):
        logger.info("scripts: %s, args: %s", scripts, args)
        self.__abort = False
        script1 = '; '.join(scripts[0])
        self.script2 = '; '.join(scripts[1])
        self.script3 = '; '.join(scripts[2])
        self.wait_for_completion = wait_for_completion
        self.args = args
        if scripts[0]:
            self.container1.execute("sh -c " + quote(script1))
        else:
            DelayTimer(10, self.execDiskOpCallback, *args)

    def finished1(self, retval=None):
        logger.info("retval = %s, __abort: %s", retval, self.__abort)
        if not self.__abort and self.script2:
            self.container2.execute("sh -c " + quote(self.script2))
        elif self.__abort and self.script3:
            self.container2.execute("sh -c " + quote(self.script3))
        elif self.__abort:
            file_op, path, target_dir, _error = self.args  # pylint: disable=W0632
            self.execDiskOpCallback(
                file_op, path, target_dir, FILE_OP_ERROR_ABORT)
        else:
            self.finished2()

    def finished2(self, retval=None):
        logger.info("retval = %s, __abort: %s", retval, self.__abort)
        if self.__abort:
            file_op, path, target_dir, _error = self.args  # pylint: disable=W0632
            self.execDiskOpCallback(
                file_op, path, target_dir, FILE_OP_ERROR_ABORT)
        elif self.wait_for_completion:
            self.execDiskOpCallback(*self.args)

    def abortFileOp(self):
        logger.info("...")
        self.__abort = True
        if self.container1 is not None and self.container1.running():
            self.container1.sendCtrlC()
        else:
            logger.error("aborting before container has started execution...")
            file_op, path, target_dir, _error = self.args  # pylint: disable=W0632
            self.execDiskOpCallback(
                file_op, path, target_dir, FILE_OP_ERROR_ABORT)
