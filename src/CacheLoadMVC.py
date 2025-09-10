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
from datetime import datetime
import six.moves.cPickle as cPickle
from Components.config import config
from Plugins.SystemPlugins.MountCockpit.MountCockpit import MountCockpit
from .Debug import logger
from .ParserEitFile import ParserEitFile
from .ParserMetaFile import ParserMetaFile
from .ServiceUtils import EXT_TS
from .FileUtils import readFile
from .FileManagerUtils import SQL_DB_MVC, FILE_TYPE_FILE
from .FileManagerUtils import FILE_IDX_FILENAME, FILE_IDX_EXT, FILE_IDX_TYPE, FILE_IDX_NAME, \
    FILE_IDX_EVENT_START_TIME, FILE_IDX_RECORDING_START_TIME, FILE_IDX_RECORDING_STOP_TIME, \
    FILE_IDX_LENGTH, FILE_IDX_DESCRIPTION, FILE_IDX_EXTENDED_DESCRIPTION, FILE_IDX_SERVICE_REFERENCE, \
    FILE_IDX_SIZE, FILE_IDX_CUTS, FILE_IDX_SORT, FILE_IDX_HOSTNAME
from .VideoUtils import getFfprobeDuration
from .CutListUtils import unpackCutList
from .CacheLoadMeta import CacheLoadMeta
from .FileUtils import deleteFile
from .ServiceUtils import ALL_VIDEO


class CacheLoadMVC(CacheLoadMeta):

    def __init__(self, plugin):
        logger.info("...")
        self.plugin = plugin
        self.database_loaded = False
        database_file = os.path.join(
            config.plugins.moviecockpit.database_directory.value, SQL_DB_MVC)
        database_load_request = os.path.join("/etc/enigma2", "." + SQL_DB_MVC)
        if not os.path.exists(database_file) or os.path.exists(database_load_request):
            logger.info("loading moviecockpit database: %s...", database_file)
            deleteFile(database_load_request)
            MountCockpit.getInstance().onInitComplete(self.loadDatabase)

        else:
            logger.info("moviecockpit database %s is loaded", database_file)
            self.database_loaded = True
        super(CacheLoadMVC, self).__init__(plugin)

    def checkFile(self, path):
        ext = os.path.splitext(path)[1]
        return ext in ALL_VIDEO

    def newDirData(self, path, file_type):
        logger.info("path: %s, file_type: %s", path, file_type)
        name = os.path.basename(path)
        sort = extended_description = ""
        if name != "..":
            sort_path = os.path.join(path, ".sort")
            if os.path.exists(sort_path):
                sort = readFile(sort_path).strip("\n")

            txt_path = path + ".txt"
            if os.path.exists(txt_path):
                extended_description = readFile(txt_path)
        afile = self.sqlInitFile()
        self.initPathData(path, afile)
        afile[FILE_IDX_TYPE] = file_type
        afile[FILE_IDX_FILENAME] = os.path.basename(path)
        afile[FILE_IDX_NAME] = afile[FILE_IDX_FILENAME]
        afile[FILE_IDX_EXTENDED_DESCRIPTION] = extended_description
        afile[FILE_IDX_LENGTH] = -1
        afile[FILE_IDX_SORT] = sort
        afile[FILE_IDX_EVENT_START_TIME] = int(time.time())
        if name != "..":
            if os.path.exists(path):
                afile[FILE_IDX_EVENT_START_TIME] = int(os.path.getmtime(path))
        afile[FILE_IDX_HOSTNAME] = self.host_name
        # logger.debug("afile: %s", afile)
        return tuple(afile)

    def newFileData(self, path):

        def parseFilename(file_name):
            name = file_name
            service_name = ""
            start_time = 0
            words = file_name.split(" - ", 2)
            date_string = words[0]
            if date_string[0:8].isdigit() and date_string[8] == " " and date_string[9:13].isdigit():
                # Default: file_name = YYYYMMDD TIME - service_name
                dt = datetime.strptime(date_string, '%Y%m%d %H%M')
                start_time = int(time.mktime(dt.timetuple()))
            if len(words) > 1:
                service_name = words[1]
            if len(words) > 2:
                name = words[2]
            cutno = ""
            if len(name) > 3:
                if name[-4] == "_" and name[-3:].isdigit():
                    cutno = name[-3:]
                    name = name[:-4]
            logger.debug("file_name: %s, start_time: %s, service_name: %s, name: %s, cutno: %s",
                         file_name, start_time, service_name, name, cutno)
            return start_time, service_name, name, cutno

        def getEitStartLength(eit, recording_start_time, recording_stop_time, recording_margin_before, recording_margin_after):
            logger.debug("recording_start_time: %s, recording_stop_time: %s, recording_margin_before: %s, recording_margin_after: %s", datetime.fromtimestamp(
                recording_start_time), datetime.fromtimestamp(recording_stop_time), recording_margin_before, recording_margin_after)
            event_start_time = eit["start"]
            event_length = eit["length"]
            event_end_time = event_start_time + event_length
            start = event_start_time
            length = event_length
            if recording_start_time:
                if recording_start_time >= event_end_time:
                    start = recording_start_time + recording_margin_before
                    length = recording_stop_time - recording_start_time - \
                        recording_margin_before - recording_margin_after
                    logger.debug("start 1: ee rs: %s, %s", start, length)
                elif recording_start_time >= event_start_time:
                    start = recording_start_time
                    length = event_length - \
                        (recording_start_time - event_start_time)
                    logger.debug("start 2: es rs: %s, %s", start, length)
            if recording_stop_time:
                if recording_stop_time <= event_end_time:
                    if recording_start_time >= event_start_time:
                        start = recording_start_time
                        length -= event_end_time - recording_stop_time
                        logger.debug(
                            "stop 1a: es re ee: %s, %s", start, length)
                    else:
                        start = event_start_time
                        length = recording_stop_time - event_start_time
                        logger.debug("stop 1b: re es: %s, %s", start, length)
            logger.debug("start: %s, length: %s",
                         datetime.fromtimestamp(start), length)
            return start, length

        def getMetaStartLength(meta, recording_start_time, recording_stop_time):
            logger.info("recording_start_time: %s, recording_stop_time: %s", datetime.fromtimestamp(
                recording_start_time), datetime.fromtimestamp(recording_stop_time))
            length = 0
            if recording_start_time and recording_stop_time:
                length = recording_stop_time - recording_start_time
            else:
                length = meta["length"]
            logger.debug("start_time: %s, length: %s",
                         datetime.fromtimestamp(recording_start_time), length)
            return recording_start_time, length

        logger.info("path: %s", path)
        file_path, ext = os.path.splitext(path)
        file_name = os.path.basename(file_path)
        name = file_name
        short_description, extended_description, service_reference, sort = "", "", "", ""
        length = 0
        cuts = cPickle.dumps(unpackCutList(readFile(path + ".cuts")))
        event_start_time = recording_stop_time = recording_start_time = int(
            os.stat(path).st_ctime)
        size = os.path.getsize(path)

        if ext in EXT_TS:
            start_time, _service_name, name, cutno = parseFilename(file_name)
            if start_time:
                event_start_time = start_time
            recording_margin_before = config.recording.margin_before.value * 60
            recording_margin_after = config.recording.margin_after.value * 60
            meta = ParserMetaFile(path).getMeta()
            if meta:
                name = meta["name"]
                short_description = meta["description"]
                service_reference = meta["service_reference"]
                recording_start_time = meta["recording_start_time"]
                recording_stop_time = meta["recording_stop_time"]
                if "recording_margin_before" in meta and meta["recording_margin_before"]:
                    recording_margin_before = meta["recording_margin_before"]
                if "recording_margin_after" in meta and meta["recording_margin_after"]:
                    recording_margin_after = meta["recording_margin_after"]
                event_start_time, length = getMetaStartLength(
                    meta, recording_start_time, recording_stop_time)
            eit = ParserEitFile(path, self.epglang).getEit()
            if eit:
                name = eit["name"]
                if name.startswith("FilmMittwoch im Ersten: "):
                    name = name[len("FilmMittwoch im Ersten: "):]
                event_start_time, length = getEitStartLength(
                    eit, recording_start_time, recording_stop_time, recording_margin_before, recording_margin_after)
                short_description = eit["short_description"]
                extended_description = eit["description"]
            if not meta and not eit:
                length = 0
                recording_start_time = int(os.stat(path).st_ctime)
                event_start_time = recording_start_time
            if cutno:
                name = "%s (%s)" % (name, cutno)
        else:
            length = getFfprobeDuration(path)
            meta = ParserMetaFile(path).getMeta()
            if meta:
                service_reference = meta["service_reference"]
                name = meta["name"]
                short_description = meta["description"]
                event_start_time = meta["rec_time"]
                if event_start_time:
                    recording_start_time = event_start_time
                    recording_stop_time = event_start_time + length
                else:
                    event_start_time = recording_stop_time = recording_start_time = int(
                        os.stat(path).st_ctime)

        txt_path = os.path.splitext(path)[0] + ".txt"
        if os.path.exists(txt_path):
            extended_description = readFile(txt_path)

        logger.debug("path: %s, name: %s, event_start_time %s, length: %s, cuts: %s",
                     path, name, datetime.fromtimestamp(event_start_time), length, cuts)

        afile = self.sqlInitFile()
        self.initPathData(path, afile)
        afile[FILE_IDX_TYPE] = FILE_TYPE_FILE
        afile[FILE_IDX_FILENAME] = file_name
        afile[FILE_IDX_EXT] = ext
        afile[FILE_IDX_NAME] = name
        afile[FILE_IDX_EVENT_START_TIME] = event_start_time
        afile[FILE_IDX_RECORDING_START_TIME] = recording_start_time
        afile[FILE_IDX_RECORDING_STOP_TIME] = recording_stop_time
        afile[FILE_IDX_LENGTH] = length
        afile[FILE_IDX_DESCRIPTION] = short_description
        afile[FILE_IDX_EXTENDED_DESCRIPTION] = extended_description
        afile[FILE_IDX_SERVICE_REFERENCE] = service_reference
        afile[FILE_IDX_SIZE] = size
        afile[FILE_IDX_CUTS] = cuts
        afile[FILE_IDX_SORT] = sort
        afile[FILE_IDX_HOSTNAME] = self.host_name
        # logger.debug("afile: %s", afile]
        return tuple(afile)
