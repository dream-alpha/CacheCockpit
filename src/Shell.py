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
from enigma import eConsoleAppContainer
from pipes import quote


class Shell():

	def __init__(self):
		logger.info("...")
		self.container = eConsoleAppContainer()
		self.container_appClosed_conn = self.container.appClosed.connect(self.finished)

	def executeShell(self, task):
		# Parameters:
		# task = (cmds, callback)
		# 	cmds = [cmd, cmd, ...]
		# 	callback = [function, arg1, arg2, ...]

		logger.info("task: %s", task)
		script, self.__callback = task
		script = quote('; '.join(script))
		self.container.execute("sh -c " + script)

	def finished(self, _retval=None):
		logger.info("retval = %s", _retval)
		if self.__callback:
			function = self.__callback[0]
			args = self.__callback[1:]
			logger.debug("function: %s, args: %s", function, args)
			if args:
				function(*args)
			else:
				function()

	def abortShell(self):
		logger.info("...")
		if self.container is not None:
			self.container.kill()
