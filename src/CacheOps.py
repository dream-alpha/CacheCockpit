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
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from .Debug import logger
from .CacheSQL import CacheSQL
from .FileManagerUtils import FILE_TYPE_DIR
from .FileManagerUtils import FILE_IDX_PATH, FILE_IDX_TYPE
from .FileManagerUtils import FILE_OP_DELETE, FILE_OP_MOVE, FILE_OP_COPY
from .CacheUtils import initPathData
from .CacheQuery import CacheQuery


class CacheOps(CacheSQL, CacheQuery):

    def __init__(self):
        logger.info("...")
        CacheSQL.__init__(self)
        CacheQuery.__init__(self, self.plugin)
        self.bookmarks = MountCockpit.getInstance().getMountedBookmarks(self.plugin)

    # row functions

    def execCacheOp(self, file_op, src_path, dst_dir):
        logger.info("file_op: %s, src_path: %s, dst_dir: %s",
                    file_op, src_path, dst_dir)
        if file_op == FILE_OP_DELETE:
            self.delete("table1", src_path)
            self.delete("table2", os.path.basename(src_path))
        elif file_op == FILE_OP_MOVE:
            self.move(src_path, dst_dir)
        elif file_op == FILE_OP_COPY:
            self.copy(src_path, dst_dir)

    def add(self, table, afile):
        # logger.info("table: %s, afile: %s", table, afile)
        self.sqlInsert(table, afile)

    def exists(self, path):
        afile = self.getFile("table1", path)
        logger.debug("path: %s, afile: %s", path, afile)
        return afile is not None

    def removeEmptyDirs(self, path):
        logger.info("path: %s", path)
        empty = not self.sqlSelect("table1", "path LIKE ?", [path + "/%"])
        while empty and path not in self.bookmarks and os.path.dirname(path) not in self.bookmarks:
            logger.debug("removing: %s", path)
            self.sqlDelete("table1", "path = ?", [path])
            path = os.path.dirname(path)
            empty = not self.sqlSelect("table1", "path LIKE ?", [path + "/%"])

    def delete(self, table, path):
        logger.debug("path: %s", path)
        if table == "table1":
            afile = self.getFile(table, path)
            if afile:
                if afile[FILE_IDX_TYPE] == FILE_TYPE_DIR:
                    self.sqlDelete(table, "path LIKE ?", [path + "%"])
                else:
                    self.sqlDelete(table, "path = ?", [path])
                if path not in self.bookmarks:
                    self.removeEmptyDirs(os.path.dirname(path))
        else:
            self.sqlDelete(table, "path LIKE ?", [path + "%"])

    def update(self, path, **kwargs):
        logger.debug("%s, kwargs: %s", path, kwargs)
        afile = self.getFile("table1", path)
        if afile:
            afile = list(afile)
            column_keys = [column.split(
                " ", 1)[0] for column in self.TABLE_COLUMNS[self.plugin]["TABLE1_COLUMNS"]]
            logger.debug("kwargs.items(): %s", list(kwargs.items()))
            for key, value in list(kwargs.items()):
                logger.debug("key: %s, value: %s", key, value)
                if key in column_keys:
                    afile[column_keys.index(key)] = value
                else:
                    logger.error("invalid column key: %s", key)
            self.add("table1", afile)

    def createDestinationDirs(self, dir_path):
        logger.info("dir_path: %s", dir_path)
        if dir_path not in self.bookmarks:
            while not self.exists(dir_path):
                logger.debug("dir_path: %s", dir_path)
                adir = self.newDirData(dir_path, FILE_TYPE_DIR)
                logger.debug("adir: %s", adir)
                self.add("table1", adir)
                dir_path = os.path.dirname(dir_path)

    def copyFile(self, src_path, dst_dir):
        logger.debug("src_path: %s, dst_dir: %s", src_path, dst_dir)
        src_file = self.getFile("table1", src_path)
        if src_file:
            dst_path = os.path.join(dst_dir, os.path.basename(src_path))
            dst_file = self.getFile("table1", dst_path)
            if dst_file is None:
                dst_file = list(src_file)
                initPathData(dst_path, dst_file, MountCockpit.getInstance(
                ).getBookmark(self.plugin, dst_path))
                logger.debug("dst_file: %s", dst_file)
                self.add("table1", dst_file)
                self.createDestinationDirs(dst_dir)
            else:
                logger.debug("dst_path: %s already exists.", dst_path)
        else:
            logger.debug("src_path: %s does not exist.", src_path)

    def copy(self, src_path, dst_path):
        logger.debug("src_path: %s, dst_dir: %s", src_path, dst_path)
        afile = self.getFile("table1", src_path)
        logger.debug("%s > %s", src_path, dst_path)
        self.copyFile(src_path, dst_path)
        if afile and afile[FILE_IDX_TYPE] == FILE_TYPE_DIR:
            file_list = self.sqlSelect(
                "table1", "path LIKE ?", [src_path + "/%"])
            for bfile in file_list:
                src_path2 = bfile[FILE_IDX_PATH]
                dst_path2 = os.path.abspath(os.path.join(
                    dst_path, os.path.relpath(src_path2, os.path.dirname(src_path))))
                logger.debug("%s > %s", src_path2, os.path.dirname(dst_path2))
                self.copyFile(src_path2, os.path.dirname(dst_path2))

    def move(self, src_path, dst_dir):
        logger.debug("src_path: %s, dst_dir: %s", src_path, dst_dir)
        if os.path.dirname(src_path) != dst_dir:
            self.copy(src_path, dst_dir)
            self.delete("table1", src_path)
