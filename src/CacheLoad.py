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


from .CacheLoadMVC import CacheLoadMVC  # noqa: F401, pylint: disable=W0611
from .CacheLoadMDC import CacheLoadMDC  # noqa: F401, pylint: disable=W0611
from .Debug import logger


class CacheLoad():

    def __init__(self, plugin):
        logger.info("...")
        exec("self.loader = CacheLoad%s(plugin)" % plugin)  # noqa: F401, pylint: disable=W0122

    def onDatabaseLoaded(self, callback=None):
        logger.info("...")
        self.loader.onDatabaseLoaded(callback)

    def onDatabaseChanged(self, callback=None):
        logger.info("...")
        self.loader.onDatabaseChanged(callback)

    def closeDatabase(self):
        logger.info("...")
        self.loader.closeDatabase()

    def cancelLoading(self):
        logger.info("...")
        self.loader.cancel()

    def clearDatabase(self):
        logger.info("...")
        self.loader.clearDatabase()

    def loadDatabase(self):
        logger.info("...")
        self.loader.loadDatabase()

    def loadDatabaseDir(self, path, recursive=False):
        logger.info("path: %s", path)
        self.loader.loadDatabaseDir(path, recursive)

    def loadDatabaseFile(self, path):
        logger.info("path: %s", path)
        self.loader.loadDatabaseFile(path)

    def newDirData(self, path, file_type):
        logger.info("path: %s, file_type: %s", path, file_type)
        return self.loader.newDirData(path, file_type)

    def getProgress(self):
        logger.info("...")
        return self.loader.getProgress()
