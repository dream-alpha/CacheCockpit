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
from .FileManagerUtils import FILE_IDX_RELPATH
from .CacheQueryMeta import CacheQueryMeta


class CacheQueryMVC(CacheQueryMeta):

    def __init__(self, plugin):
        logger.info("...")
        super(CacheQueryMVC, self).__init__(plugin)
        self.plugin = plugin

    def getFileList(self, adir, recursive=False):
        logger.debug("adir: %s, recursive: %s", adir, recursive)
        file_list = []
        afile = self.getFile("table1", adir)
        if afile:
            rel_dir = afile[FILE_IDX_RELPATH]
            logger.debug("rel_dir: %s", rel_dir)
            wildcard = "%" if recursive else ""
            where = "rel_dir LIKE ?"
            if "trashcan" not in rel_dir:
                where += " AND rel_dir NOT LIKE '%trashcan%'"
            where += " AND file_type = ?"
            file_list = self.sqlSelect(
                "table1", where, [rel_dir + wildcard, FILE_TYPE_FILE])
        return file_list

    def getDirListAll(self, adir, recursive=False):
        logger.debug("adir: %s", adir)
        dir_list = []
        afile = self.getFile("table1", adir)
        if afile:
            rel_dir = afile[FILE_IDX_RELPATH]
            logger.debug("rel_dir: %s", rel_dir)
            file_types = [FILE_TYPE_DIR, FILE_TYPE_LINK]
            types = ",".join("?" * len(file_types))
            wildcard = ""
            if recursive:
                wildcard = "%" if rel_dir.endswith("/") else "/%"
            where = "path != bookmark"
            where += " AND file_name != 'trashcan'"
            where += " AND rel_path LIKE ?"
            if "trashcan" not in rel_dir:
                where += " AND rel_dir NOT LIKE '%trashcan%'"
            where += " AND file_type IN ({})".format(types)
            dir_list = self.sqlSelect(
                "table1", where, [rel_dir + wildcard] + file_types)
        return dir_list

    def getDirList(self, adir, recursive=False):
        logger.debug("adir: %s, recursive: %s", adir, recursive)
        dir_list = []
        afile = self.getFile("table1", adir)
        if afile:
            rel_dir = afile[FILE_IDX_RELPATH]
            logger.debug("rel_dir: %s", rel_dir)
            wildcard = ""
            if recursive:
                wildcard = "%" if rel_dir.endswith("/") else "/%"
            max_col = "event_start_time" if self.plugin == "MVC" else "date"
            query = """
                SELECT t1.* FROM table1 t1
                JOIN (
                    SELECT directory, rel_path, rel_dir, MAX(%s) AS max_%s
                        FROM table1
                            WHERE rel_dir LIKE ? AND path != bookmark AND file_name != "trashcan" AND file_type > ? GROUP BY rel_path
                     ) t2
                     ON t1.rel_path = t2.rel_path AND t1.%s = t2.max_%s
                GROUP BY t1.rel_path
                ORDER BY t1.directory ASC;
            """ % ((max_col,) * 4)
            dir_list = self.sqlSelectRaw(
                query, (rel_dir + wildcard, FILE_TYPE_FILE))
        return dir_list
