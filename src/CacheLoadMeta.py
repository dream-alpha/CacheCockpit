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
import socket
import abc
from Components.config import config
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from .Debug import logger
from .FileUtils import readFile
from .DelayTimer import DelayTimer
from .FileManagerUtils import FILE_TYPE_DIR, FILE_TYPE_LINK
from .CacheOps import CacheOps
from .FileManagerUtils import FILE_OP_LOAD
from .CacheUtils import initPathData


class CacheLoadMeta(CacheOps, object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, plugin):
        logger.info("plugin: %s", plugin)
        self.plugin = plugin
        self.database_loaded_callback = None
        self.database_changed_callback = None
        self.epglang = config.plugins.moviecockpit.epglang.value
        self.bookmarks = MountCockpit.getInstance().getMountedBookmarks(self.plugin)
        CacheOps.__init__(self)
        self.files_total = 0
        self.files_done = 0
        self.file_name = ""
        self.cancel_request = False
        self.host_name = socket.gethostname()

    def onDatabaseLoaded(self, callback=None):
        logger.info("...")
        self.database_loaded_callback = callback
        if self.database_loaded:
            self.onDatabaseLoadedCallback()

    def onDatabaseLoadedCallback(self):
        logger.info("...")
        if self.database_loaded_callback:
            self.database_loaded_callback()

    def onDatabaseChanged(self, callback=None):
        logger.info("...")
        self.database_changed_callback = callback

    def onDatabaseChangedCallback(self):
        if self.database_changed_callback:
            self.database_changed_callback()

    def cancel(self):
        logger.info("..")
        self.cancel_request = True

    def closeDatabase(self):
        logger.debug("...")
        self.sqlClose()

    def clearDatabase(self):
        logger.debug("...")
        self.sqlClearDatabase()
        self.database_loaded = False

    def getProgress(self):
        logger.debug("files_total: %s, files_done: %s",
                     self.files_total, self.files_done)
        percent = 100
        if self.files_total:
            percent = int(float(self.files_done) / float(self.files_total) * 100)
        return self.files_total - self.files_done, self.file_name, FILE_OP_LOAD, percent

    def loadDatabase(self):
        self.database_loaded = False
        self.bookmarks = MountCockpit.getInstance().getMountedBookmarks(self.plugin)
        dirs = self.bookmarks
        logger.info("dirs: %s", dirs)
        if dirs:
            self.clearDatabase()
            self.load_list = self.getDirsLoadList(dirs)
            self.files_total = len(self.load_list)
            self.files_done = 0
            self.file_name = ""
            DelayTimer(10, self.nextFileOp)

    def loadDatabaseDir(self, adir, recursive=False):
        logger.info("adir: %s", adir)
        self.database_loaded = False
        if adir:
            self.delete("table1", adir)
            self.load_list = self.getDirsLoadList([adir], recursive)
            self.files_total = len(self.load_list)
            self.files_done = 0
            self.file_name = ""
            DelayTimer(10, self.nextFileOp)

    def nextFileOp(self):
        logger.info("...")
        if self.load_list and not self.cancel_request:
            path = self.load_list.pop(0)
            self.file_name = os.path.basename(path)
            self.loadDatabaseFile(path)
            self.files_done += 1
            DelayTimer(10, self.nextFileOp)
        else:
            logger.debug("done.")
            if self.cancel_request:
                self.files_total = 0
                self.files_done = 0
                self.cancel_request = False
            else:
                self.database_loaded = True
            self.onDatabaseLoadedCallback()

    def loadDatabaseCover(self, path):
        logger.info("path: %s", path)
        afile = self.newCoverData(path)
        if afile:
            self.add("table2", afile)

    def loadDatabaseFile(self, path):
        logger.info("path: %s", path)
        afile = ()
        if os.path.isfile(path):
            afile = self.newFileData(path)
        elif os.path.islink(path):
            afile = self.newDirData(path, FILE_TYPE_LINK)
        elif os.path.isdir(path):
            afile = self.newDirData(path, FILE_TYPE_DIR)
        if afile:
            self.add("table1", afile)
            self.loadDatabaseCover(path)
            if self.database_loaded:
                self.onDatabaseChangedCallback()

    def newCoverData(self, path):
        logger.info("path: %s", path)
        logger.debug("trying: %s", os.path.splitext(path)[0] + ".jpg")
        afile = None
        cover = readFile(os.path.splitext(path)[0] + ".jpg")
        if cover:
            cover_name = os.path.basename(path)
            afile = (cover_name, cover)
        else:
            cover_name = os.path.basename(path)
            cover_path = os.path.join(path, cover_name + ".jpg")
            logger.debug("trying: %s", cover_path)
            cover = readFile(cover_path)
            if cover:
                afile = (cover_name, cover)
        if afile:
            logger.debug("found cover_name: %s", cover_name)
        return afile

    def initPathData(self, path, afile):
        logger.info("path: %s", path)
        bookmark = MountCockpit.getInstance().getBookmark(self.plugin, path)
        initPathData(path, afile, bookmark)

    @abc.abstractmethod
    def newDirData(self, path, file_type):
        pass

    @abc.abstractmethod
    def newFileData(self, path):
        pass

    @abc.abstractmethod
    def checkFile(self, path):
        pass

    def __getDirLoadList(self, adir, load_list, recursive):
        logger.debug("adir: %s", adir)
        if os.path.exists(adir):
            for file_name in os.listdir(adir):
                path = os.path.join(adir, file_name)
                if os.path.isfile(path):
                    if self.checkFile(path):
                        load_list.append(path)
                else:
                    load_list.append(path)
                    if recursive:
                        self.__getDirLoadList(path, load_list, recursive)
        else:
            logger.error("adir does not exist: %s", adir)
        # logger.debug("load_list: %s", load_list)

    def getDirsLoadList(self, dirs, recursive=True):
        logger.info("dirs: %s", dirs)
        load_list = []
        for adir in dirs:
            load_list.append(adir)
            self.__getDirLoadList(adir, load_list, recursive)
        return load_list
