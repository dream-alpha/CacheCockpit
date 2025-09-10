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


from .Debug import logger
from .FileManagerUtils import FILE_TYPE_FILE, FILE_TYPE_DIR, FILE_TYPE_LINK
from .CacheQueryMeta import CacheQueryMeta


class CacheQueryMDC(CacheQueryMeta):

    def __init__(self, plugin):
        logger.info("...")
        super(CacheQueryMDC, self).__init__(plugin)
        self.plugin = plugin

    def getFileList(self, adir, recursive=False):
        logger.debug("adir: %s, recursive: %s", adir, recursive)
        file_list = []
        afile = self.getFile("table1", adir)
        if afile:
            wildcard = "/%" if recursive else ""
            where = "directory LIKE ?"
            where += " AND file_type = ?"
            file_list = self.sqlSelect(
                "table1", where, [adir + wildcard, FILE_TYPE_FILE])
        return file_list

    def getFileListByList(self, alist):
        query = "SELECT * FROM table1 WHERE path IN (%s)" % ','.join([
            '?'] * len(alist))
        file_list = self.sqlSelectRaw(query, alist)
        return file_list

    def getDirListAll(self, adir, recursive=False):
        logger.debug("adir: %s", adir)
        dir_list = []
        afile = self.getFile("table1", adir)
        if afile:
            file_types = [FILE_TYPE_DIR, FILE_TYPE_LINK]
            types = ",".join("?" * len(file_types))
            wildcard = "/%" if recursive else ""
            where = "path != bookmark"
            where += " AND directory LIKE ?"
            where += " AND file_type IN ({})".format(types)
            dir_list = self.sqlSelect(
                "table1", where, [adir + wildcard] + file_types)
        return dir_list

    def getDirList(self, adir, recursive=False):
        logger.debug("adir: %s", adir)
        return self.getDirListAll(adir, recursive)
