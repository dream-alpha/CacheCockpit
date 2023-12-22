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


from datetime import datetime
from .Debug import logger
from .MovieCoverUNIDownload import MovieCoverUNIDownload
from .WebRequests import WebRequests


class MovieCoverTVHDownload(WebRequests, MovieCoverUNIDownload):

	def __init__(self):
		WebRequests.__init__(self)
		MovieCoverUNIDownload.__init__(self)

	def getCoverUrl(self, channel_id, event_start):
		url = "http://mobile.hoerzu.de/programbystation"
		data = []
		data.append("channels: [%s]" % channel_id)
		data.append("date: %s" % event_start)
		params = {"data": data}
		logger.debug("url: %s, params: %s", url, params)
		return url, params

	def parseEvents(self, channel_id, content, event_start, length):
		logger.info("...")
		# logger.debug("content: %s", str(content))
		cover_url = ""
		cover_title = "n/a"
		if content:
			for events in content:
				if str(events["id"]) == channel_id:
					broadcasts = events.get("broadcasts", [])
					for event in broadcasts:
						title = event.get("title", "n/a")
						timestart = event.get("startTime", 0)
						url = event.get("pic", "")
						logger.debug(">>> timestart: %s, event_start: %s, length: %s", datetime.fromtimestamp(timestart), datetime.fromtimestamp(event_start), length)
						if not self.findEvent(timestart, event_start, length):
							logger.debug("saving: title: %s, url: %s", title, url)
							cover_url = url
							cover_title = title
						else:
							logger.debug(">>> break: url: %s, title: %s", cover_url, cover_title)
							break
					else:
						cover_url = ""
						cover_title = "n/a"
			logger.debug(">>> cover_title: %s, cover_url: %s", cover_title, cover_url)
		return cover_url
