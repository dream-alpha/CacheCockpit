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
import abc
from Components.config import config
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from .Debug import logger
from .CacheSQL import CacheSQL
from .FileManagerUtils import FILE_TYPE_FILE, FILE_TYPE_DIR, FILE_TYPE_LINK
from .FileManagerUtils import FILE_IDX_RELPATH, FILE_IDX_SIZE, FILE_IDX_SORT


class CacheQueryMeta(CacheSQL, object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, plugin):
        logger.info("...")
        self.plugin = plugin
        CacheSQL.__init__(self)
        self.bookmarks = MountCockpit.getInstance().getMountedBookmarks(self.plugin)

    def getFile(self, table, path):
        logger.debug("table: %s, path: %s", table, path)
        afile = None
        file_list = self.sqlSelect(table, "path = ?", [path])
        if file_list:
            if len(file_list) == 1:
                afile = file_list[0]
            else:
                logger.error("not a single response: %s", file_list)
        return afile

    @abc.abstractmethod
    def getFileList(self, adir, recursive=False):
        pass

    @abc.abstractmethod
    def getDirListAll(self, adir, recursive=False):
        pass

    @abc.abstractmethod
    def getDirList(self, adir, recursive=False):
        pass

    def getDirNamesList(self, adir):
        logger.info("adir: %s", adir)
        file_types = [FILE_TYPE_DIR, FILE_TYPE_LINK]
        types_bindings = ",".join("?" * len(file_types))
        afile = self.getFile("table1", adir)
        rel_path = afile[FILE_IDX_RELPATH]
        where = "file_name != 'trashcan'"
        where += " AND rel_dir = ?"
        where += " AND file_type IN ({})".format(types_bindings)
        alist = self.sqlSelectDistinct(
            "table1", "file_name", where, [rel_path] + file_types)
        dir_names_list = [item[0] for item in alist]
        logger.debug("dir_names_list: %s", dir_names_list)
        return dir_names_list

    def getCountSize(self, path):
        logger.info("path: %s", path)
        total_count = total_size = 0
        if not os.path.basename(path) == "..":
            afile = self.getFile("table1", path)
            if afile:
                rel_path = afile[FILE_IDX_RELPATH]
                logger.debug("rel_path: %s", rel_path)
                if rel_path == "/":
                    rel_path = ""
                file_list = self.sqlSelect("table1", "rel_path LIKE ? AND file_type = ?", [rel_path + "/%", FILE_TYPE_FILE])
                for afile in file_list:
                    total_count += 1
                    total_size += afile[FILE_IDX_SIZE]
        logger.debug("path: %s, total_count: %s, total_size: %s",
                     path, total_count, total_size)
        return total_count, total_size

    def getSortMode(self, adir):
        logger.info("adir: %s", adir)
        sort = ""
        timestamp = 0
        afile = self.getFile("table1", adir)
        if afile:
            rel_path = afile[FILE_IDX_RELPATH]
            where = "rel_path = ?"
            where += " AND file_type = ?"
            alist = self.sqlSelect("table1", where, [rel_path, FILE_TYPE_DIR])
            for afile in alist:
                data = afile[FILE_IDX_SORT].split(",")
                if len(data) > 1 and int(data[0]) > timestamp:
                    sort = data[1]
                    timestamp = int(data[0])
        if not sort:
            logger.debug("using default sort")
            sort = config.plugins.moviecockpit.list_sort.value
        logger.debug("sort: %s", sort)
        return sort
