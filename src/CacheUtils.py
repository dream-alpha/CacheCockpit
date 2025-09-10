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
from FileManagerUtils import FILE_IDX_BOOKMARK, FILE_IDX_PATH, FILE_IDX_DIR, FILE_IDX_RELPATH, FILE_IDX_RELDIR


def initPathData(path, afile, bookmark):
    afile[FILE_IDX_BOOKMARK] = bookmark
    afile[FILE_IDX_PATH] = path
    afile[FILE_IDX_DIR] = os.path.dirname(path)
    relpath = os.path.abspath(os.path.relpath(path, afile[FILE_IDX_BOOKMARK]))
    afile[FILE_IDX_RELPATH] = relpath
    afile[FILE_IDX_RELDIR] = os.path.dirname(
        afile[FILE_IDX_RELPATH]) if relpath != "/" else relpath
