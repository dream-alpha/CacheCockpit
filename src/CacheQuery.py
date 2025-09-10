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


from .CacheQueryMVC import CacheQueryMVC  # noqa: F401, pylint: disable=W0611
from .CacheQueryMDC import CacheQueryMDC  # noqa: F401, pylint: disable=W0611
from .Debug import logger


class CacheQuery():

    def __init__(self, plugin):
        logger.info("...")
        exec("self.query = CacheQuery%s(plugin)" % plugin)  # noqa: F401, pylint: disable=W0122

    def getFile(self, table, path):
        logger.debug("table: %s, path: %s", table, path)
        return self.query.getFile(table, path)

    def getFileList(self, adir, recursive=False):
        logger.debug("adir: %s, recursive: %s", adir, recursive)
        return self.query.getFileList(adir, recursive)

    def getFileListByList(self, alist):
        logger.debug("...")
        return self.query.getFileListByList(alist)

    def getDirListAll(self, adir, recursive=False):
        logger.debug("adir: %s", adir)
        return self.query.getDirListAll(adir, recursive)

    def getDirList(self, adir, recursive=False):
        logger.debug("adir: %s, recursive: %s", adir, recursive)
        return self.query.getDirList(adir, recursive)

    def getDirNamesList(self, adir):
        return self.query.getDirNamesList(adir)

    def getCountSize(self, path):
        logger.info("path: %s", path)
        return self.query.getCountSize(path)

    def getSortMode(self, adir):
        logger.info("adir: %s", adir)
        return self.query.getSortMode(adir)
