#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2022 by dream-alpha
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

# file manager ops
FILE_OP_DELETE = 1
FILE_OP_MOVE = 2
FILE_OP_COPY = 3
FILE_OP_LOAD = 4 # loadDatabaseCache

# file manager errors
FILE_OP_ERROR_NONE = 0
FILE_OP_ERROR_NO_DISKSPACE = 1
FILE_OP_ERROR_ABORT = 2
FILE_OP_ERROR = 100

# database file
SQL_DB_NAME = "/etc/enigma2/cachecockpit.db"

# file types
FILE_TYPE_FILE = 1
FILE_TYPE_DIR = 2
FILE_TYPE_LINK = 3

# recordings indexes
FILE_IDX_DIR = 0
FILE_IDX_TYPE = 1
FILE_IDX_PATH = 2
FILE_IDX_FILENAME = 3
FILE_IDX_EXT = 4
FILE_IDX_NAME = 5
FILE_IDX_EVENT_START_TIME = 6
FILE_IDX_RECORDING_START_TIME = 7
FILE_IDX_RECORDING_STOP_TIME = 8
FILE_IDX_LENGTH = 9
FILE_IDX_DESCRIPTION = 10
FILE_IDX_EXTENDED_DESCRIPTION = 11
FILE_IDX_SERVICE_REFERENCE = 12
FILE_IDX_SIZE = 13
FILE_IDX_CUTS = 14
FILE_IDX_TAGS = 15

# covers indexes
COVER_IDX_FILENAME = 0
COVER_IDX_COVER = 1
