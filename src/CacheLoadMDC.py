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
import time
import json
from datetime import datetime
from Components.config import config
from .CacheLoadMeta import CacheLoadMeta
from .Debug import logger
from .FileManagerUtils import MDC_TYPE_FILE
from .FileManagerUtils import MDC_MEDIA_TYPE_DIR, MDC_MEDIA_TYPE_PLAYLIST, MDC_MEDIA_TYPE_PICTURE, MDC_MEDIA_TYPE_MOVIE, MDC_MEDIA_TYPE_MUSIC
from .FileManagerUtils import SQL_DB_MDC, MDC_IDX_FILENAME, MDC_IDX_EXT, MDC_IDX_TYPE, MDC_IDX_NAME, \
    MDC_IDX_META, MDC_IDX_MEDIA, MDC_IDX_DATE
from .PictureUtils import getExifData, transformPicture
from .ServiceUtils import ALL_MEDIA, EXT_PICTURE, ALL_VIDEO, EXT_MUSIC, EXT_PLAYLIST
from .Thumbnail import Thumbnail
from .FileUtils import deleteFile


class CacheLoadMDC(CacheLoadMeta, Thumbnail):

    def __init__(self, plugin):
        logger.info("...")
        super(CacheLoadMDC, self).__init__(plugin)
        Thumbnail.__init__(self)
        self.create_thumbnails = config.plugins.mediacockpit.create_thumbnails.value
        self.plugin = plugin
        self.database_loaded = False
        database_file = os.path.join(
            config.plugins.mediacockpit.database_directory.value, SQL_DB_MDC)
        database_load_request = os.path.join("/etc/enigma2", "." + SQL_DB_MDC)
        if not os.path.exists(database_file) or os.path.exists(database_load_request):
            logger.info("loading mediacockpit database...")
            deleteFile(database_load_request)
            # MountCockpit.getInstance().onInitComplete(self.loadDatabase)
        else:
            logger.info("mediacockpit database is loaded")
            self.database_loaded = True

    def checkFile(self, path):
        filename, ext = os.path.splitext(os.path.basename(path))
        return not filename.startswith(".") and not filename.endswith((".transformed", ".thumbnail", "backdrop")) and ext.lower() in ALL_MEDIA

    def newDirData(self, path, file_type):
        logger.info("path: %s, file_type: %s", path, file_type)
        afile = self.sqlInitFile()
        exif_data = {}
        self.initPathData(path, afile)
        afile[MDC_IDX_TYPE] = file_type
        afile[MDC_IDX_FILENAME] = os.path.basename(path)
        afile[MDC_IDX_NAME] = afile[MDC_IDX_FILENAME]
        afile[MDC_IDX_MEDIA] = MDC_MEDIA_TYPE_DIR
        afile[MDC_IDX_META] = json.dumps(exif_data)
        logger.debug("afile: %s", afile)
        return tuple(afile)

    def getEpochTimestamp(self, path, exif_data):
        date_time = None
        if "DateTimeOriginal" in exif_data:
            date_time = str(exif_data["DateTimeOriginal"])
        for time_format in ["%Y:%m:%d %H:%M:%S", "%m:%d:%Y %H:%M"]:
            try:
                time_tuple = time.strptime(date_time, time_format)
                time_epoch = int(time.mktime(time_tuple))
                break
            except Exception:
                stat = os.stat(path)
                time_epoch = int(stat.st_mtime)
        return time_epoch

    def newFileData(self, path):
        logger.info("path: %s", path)
        media_type = -1
        file_path, ext = os.path.splitext(path)
        file_name = os.path.basename(file_path)
        ext = ext.lower()
        time_epoch = 0
        exif_data = {}
        if ext in EXT_PICTURE:
            exif_data = getExifData(path)
            time_epoch = self.getEpochTimestamp(path, exif_data)
            media_type = MDC_MEDIA_TYPE_PICTURE
            if not os.path.exists(file_name + ".transformed" + ext):
                transformPicture(path, exif_data["Orientation"])
            if self.create_thumbnails and not os.path.exists(file_name + ".thumbnail" + ext):
                self.createThumbnail(path)
        elif ext in ALL_VIDEO:
            media_type = MDC_MEDIA_TYPE_MOVIE
        elif ext in EXT_MUSIC:
            media_type = MDC_MEDIA_TYPE_MUSIC
        elif ext in EXT_PLAYLIST:
            media_type = MDC_MEDIA_TYPE_PLAYLIST

        logger.debug("path: %s, file_name: %s, time_epoch %s, media_type: %s",
                     path, file_name, datetime.fromtimestamp(time_epoch), media_type)

        afile = self.sqlInitFile()
        self.initPathData(path, afile)
        logger.debug("afile 1: %s", afile)
        afile[MDC_IDX_TYPE] = MDC_TYPE_FILE
        afile[MDC_IDX_FILENAME] = file_name
        afile[MDC_IDX_EXT] = ext
        afile[MDC_IDX_NAME] = file_name
        afile[MDC_IDX_DATE] = time_epoch
        afile[MDC_IDX_MEDIA] = media_type
        afile[MDC_IDX_META] = json.dumps(exif_data)
        logger.debug("afile: %s", afile)
        return tuple(afile)
