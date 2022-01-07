#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2023 by dream-alpha
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
from Components.config import config
from .Debug import logger
from .MovieCoverTVSDownload import MovieCoverTVSDownload
from .MovieCoverTVMDownload import MovieCoverTVMDownload
from .MovieCoverTVFADownload import MovieCoverTVFADownload
from .MovieCoverTVHDownload import MovieCoverTVHDownload
from .WebRequests import WebRequests
from .FileUtils import writeFile, createDirectory


class MovieCoverDownload(MovieCoverTVSDownload, MovieCoverTVMDownload, MovieCoverTVHDownload, MovieCoverTVFADownload, WebRequests):

	def __init__(self):
		MovieCoverTVSDownload.__init__(self)
		MovieCoverTVMDownload.__init__(self)
		MovieCoverTVHDownload.__init__(self)
		MovieCoverTVFADownload.__init__(self)
		WebRequests.__init__(self)
		self.cover_sources_prio = ["tvs_id", "tvm_id", "tvfa_id", "tvh_id"]
		self.cover_sources = {
			"tvh_id": MovieCoverTVHDownload,
			"tvs_id": MovieCoverTVSDownload,
			"tvm_id": MovieCoverTVMDownload,
			"tvfa_id": MovieCoverTVFADownload
		}

	def getCoverPath(self, path):
		cover_path = os.path.splitext(path)[0] + ".jpg"
		logger.debug("cover_path: %s", cover_path)
		return cover_path

	def downloadCover(self, cover_url, cover_path):
		logger.info("cover_path: %s, cover_url: %s", cover_path, cover_url)
		cover_found = 0
		if cover_url and cover_path:
			cover_dir = os.path.dirname(cover_path)
			if not os.path.exists(cover_dir):
				createDirectory(cover_dir)
			r_content = self.getContent(cover_url)
			if r_content:
				writeFile(cover_path, r_content)
				cover_found = 1
		return cover_found

	def getMovieCover(self, path, service_ref, title="", event_start=0, length=0):
		logger.info("path: %s, title: %s", path, title)
		cover_url = ""
		if config.plugins.moviecockpit.cover_source.value == "auto":
			for cover_source in self.cover_sources_prio:
				cover_url = self.cover_sources[cover_source]().getSourceMovieCover(path, cover_source, service_ref, title, event_start, length)
				if cover_url:
					break
		else:
			cover_source = config.plugins.moviecockpit.cover_source.value
			cover_url = self.cover_sources[cover_source]().getSourceMovieCover(path, cover_source, service_ref, title, event_start, length)
		if cover_url:
			cover_path = self.getCoverPath(path)
			self.downloadCover(cover_url, cover_path)
