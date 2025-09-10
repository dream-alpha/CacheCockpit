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
from .Debug import logger
from .FileManager import FileManager
from .FileManagerUtils import FILE_IDX_NAME, FILE_OP_MOVE


class RecordingSeries():

    def __init__(self):
        self.block_paths = []

    def addBlock(self, path):
        logger.info("path: %s", path)
        self.block_paths.append(path)

    def removeBlock(self, path):
        logger.info("path: %s", path)
        if path:
            if path in self.block_paths:
                self.block_paths.remove(path)
        else:
            self.block_paths = []

    def getSeriesDir(self, name):
        logger.info("name: %s", name)
        parts = []
        dirname = name
        for separator in [": ", " - ", " ("]:
            if separator in name:
                parts = name.split(separator)
                break
        if len(parts) > 1:
            dirname = parts[0]
        logger.info("dirname: %s", dirname)
        return dirname

    def checkSeriesDir(self, name, adir):
        dir_names = FileManager.getInstance("MVC").getDirNamesList(adir)
        for dir_name in dir_names:
            if name.startswith(dir_name):
                logger.debug("dir_name: %s", dir_name)
                break
        else:
            dir_name = ""
        return dir_name

    def moveToSeriesDir(self, path):
        logger.info("path: %s, block_paths: %s", path, self.block_paths)
        if path not in self.block_paths:
            afile = FileManager.getInstance("MVC").getFile("table1", path)
            if afile:
                adir = os.path.dirname(path)
                dirname = self.checkSeriesDir(afile[FILE_IDX_NAME], adir)
                if dirname:
                    dstdir = os.path.join(adir, dirname)
                    logger.debug("moving: %s to %s", path, dstdir)
                    FileManager.getInstance("MVC").execFileOp(
                        FILE_OP_MOVE, path, dstdir, self.execFileOpCallback)

    def execFileOpCallback(self, file_op, path, target_dir, error):
        logger.info("file_op: %s, path: %s, target_dir: %s, error: %s",
                    file_op, path, target_dir, error)
        FileManager.getInstance("MVC").loadDatabaseFile(target_dir)
        FileManager.getInstance("MVC").onDatabaseChangedCallback()
        self.removeBlock(path)
