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
from collections import deque
from pipes import quote


class Shell():

	def __init__(self):
		self.container = eConsoleAppContainer()
		self.container_appClosed_conn = self.container.appClosed.connect(self.finished)
		self.tasks = deque()
		self.busy = False

	def executeShell(self, task):
		# Parameters:
		# task = (cmds, callback)
		# 	cmds = [cmd, cmd]
		# 	callback = [function, arg1, arg2, ...]

		logger.debug("task: %s", str(task))
		self.tasks.append(task)
		if not self.busy:
			self.execute()
		else:
			logger.debug("busy")

	def execute(self):
		script, self.__callback = self.tasks.popleft()
		if script:
			script = '; '.join(script)
			script = quote(script)
			logger.debug("script: %s", script)
			self.container.execute("sh -c " + script)
			self.busy = True

	def finished(self, _retval=None):
		logger.debug("retval = %s", str(_retval))
		self.busy = False
		if self.__callback:
			if isinstance(self.__callback, list):
				function = self.__callback[0]
				args = self.__callback[1:]
				logger.debug("function: %s, args: %s", function, args)
				if function:
					if args:
						function(*args)
					else:
						function()
			else:
				logger.error("callback must be a list")
		if self.tasks:
			logger.debug("more script(s) to execute")
			self.execute()

	def abortShell(self):
		logger.debug("...")
		if self.container is not None:
			self.container.kill()
		self.tasks = deque()
		self.busy = False
