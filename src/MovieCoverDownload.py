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


from Debug import logger
from Components.config import config
from MovieCoverUtils import getCoverPath
from MovieCoverTVSDownload import MovieCoverTVSDownload
from MovieCoverTVMDownload import MovieCoverTVMDownload
from MovieCoverTVFADownload import MovieCoverTVFADownload
from MovieCoverTVHDownload import MovieCoverTVHDownload
from MovieCover import MovieCover


class MovieCoverDownload(MovieCover, MovieCoverTVSDownload, MovieCoverTVMDownload, MovieCoverTVHDownload, MovieCoverTVFADownload):

	def __init__(self):
		MovieCover.__init__(self)
		MovieCoverTVSDownload.__init__(self)
		MovieCoverTVMDownload.__init__(self)
		MovieCoverTVHDownload.__init__(self)
		MovieCoverTVFADownload.__init__(self)
		self.cover_sources_prio = ["tvs_id", "tvm_id", "tvfa_id", "tvh_id"]
		self.cover_sources = {
			"tvh_id": MovieCoverTVHDownload,
			"tvs_id": MovieCoverTVSDownload,
			"tvm_id": MovieCoverTVMDownload,
			"tvfa_id": MovieCoverTVFADownload
		}

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
			cover_path, _backdrop_path, _info_path = getCoverPath(path)
			self.downloadCover(cover_url, cover_path)
