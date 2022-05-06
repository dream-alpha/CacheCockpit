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
from FileUtils import createDirectory, writeFile, deleteFile
from WebRequests import WebRequests


class MovieCover(WebRequests):

	def __init__(self):
		WebRequests.__init__(self)

	def downloadCover(self, cover_url, cover_path, backdrop_url=None, backdrop_path=None):
		logger.info("cover_path: %s, cover_url: %s", cover_path, cover_url)
		logger.info("backdrop_path: %s, backdrop_url: %s", backdrop_path, backdrop_url)
		cover_found = 0
		if cover_url and cover_path:
			cover_dir = os.path.dirname(cover_path)
			if not os.path.exists(cover_dir):
				createDirectory(cover_dir)
			deleteFile(cover_path)
			r_content = self.getContent(cover_url)
			if r_content:
				writeFile(cover_path, r_content)
				cover_found = 1
		if backdrop_url and backdrop_path:
			backdrop_dir = os.path.dirname(backdrop_path)
			if not os.path.exists(backdrop_dir):
				createDirectory(backdrop_dir)
			deleteFile(backdrop_path)
			r_content = self.getContent(backdrop_url)
			if r_content:
				writeFile(backdrop_path, r_content)
		return cover_found
