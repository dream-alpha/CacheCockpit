#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2024 by dream-alpha
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
from .DelayTimer import DelayTimer


class MovieCoverDownload(MovieCoverTVSDownload, MovieCoverTVMDownload, MovieCoverTVHDownload, MovieCoverTVFADownload, WebRequests):

	def __init__(self):
		MovieCoverTVSDownload.__init__(self)
		MovieCoverTVMDownload.__init__(self)
		MovieCoverTVHDownload.__init__(self)
		MovieCoverTVFADownload.__init__(self)
		WebRequests.__init__(self)
		self.cover_source_ids = []
		self.cover_sources = {
			"tvh_id": MovieCoverTVHDownload,
			"tvs_id": MovieCoverTVSDownload,
			"tvm_id": MovieCoverTVMDownload,
			"tvfa_id": MovieCoverTVFADownload
		}

	def downloadCover(self, path, service_ref, title, event_start, length, callback):
		logger.info("...")
		if self.cover_source_ids:
			cover_source_id = self.cover_source_ids.pop(0)
			logger.debug("cover_source_id: %s", cover_source_id)
			cover_url = self.cover_sources[cover_source_id]().getSourceMovieCover(path, cover_source_id, service_ref, title, event_start, length)
			if cover_url:
				if self.downloadFile(cover_url, os.path.splitext(path)[0] + ".jpg"):
					callback(path)
					return
			DelayTimer(50, self.downloadCover, path, service_ref, title, event_start, length, callback)
		else:
			callback(path)
		return

	def getMovieCover(self, path, service_ref, title="", event_start=0, length=0, cover_source_id="", callback=None):
		logger.info("path: %s, title: %s, cover_source_id: %s", path, title, cover_source_id)
		if not cover_source_id:
			cover_source_id = config.plugins.moviecockpit.cover_source.value
		if cover_source_id == "auto":
			self.cover_source_ids = ["tvs_id", "tvm_id", "tvfa_id", "tvh_id"]
		else:
			self.cover_source_ids = [cover_source_id]
		DelayTimer(50, self.downloadCover, path, service_ref, title, event_start, length, callback)
