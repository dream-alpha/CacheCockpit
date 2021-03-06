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


import os
from Debug import logger


def getCoverPath(path):
	logger.debug("path: %s", path)
	base = os.path.splitext(path)[0]
	cover_path = base + ".jpg"
	backdrop_path = base + ".backdrop.jpg"
	info_path = base + ".txt"
	logger.debug("cover_path: %s, backdrop_path: %s, info_path: %s", cover_path, backdrop_path, info_path)
	return cover_path, backdrop_path, info_path
