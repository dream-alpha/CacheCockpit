#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2023 by dream-alpha
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


from Components.config import config
from Tools.BoundFunction import boundFunction
from .Debug import logger
from .DelayTimer import DelayTimer
from .FileManager import FileManager


instance = None


class Trashcan():

	def __init__(self):
		self.__schedulePurge()

	@staticmethod
	def getInstance():
		global instance
		if instance is None:
			instance = Trashcan()
		return instance

	def __schedulePurge(self):
		if config.plugins.moviecockpit.trashcan_enable.value and config.plugins.moviecockpit.trashcan_clean.value:
			# next cleanup in 24 hours
			seconds = 24 * 60 * 60
			DelayTimer(1000 * seconds, self.__schedulePurge)
			# execute cleanup
			DelayTimer(10000, boundFunction(FileManager.getInstance().purgeTrashcan, config.plugins.moviecockpit.trashcan_retention.value))
			logger.info("next trashcan cleanup in %s minutes", seconds / 60)
