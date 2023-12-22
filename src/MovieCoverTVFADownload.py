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


import time
from datetime import datetime
from .Debug import logger
from .MovieCoverUNIDownload import MovieCoverUNIDownload
from .WebRequests import WebRequests


class MovieCoverTVFADownload(WebRequests, MovieCoverUNIDownload):

	def __init__(self):
		WebRequests.__init__(self)
		MovieCoverUNIDownload.__init__(self)

	def getCoverUrl(self, _channel_id, _event_start):
		to_time = datetime.now().strftime("%Y-%m-%d")
		url = "https://tvfueralle.de/api/broadcasts/%s" % to_time
		logger.debug("url: %s", url)
		return url, []

	def parseEvents(self, channel_id, content, event_start, length):
		logger.info("...")
		# logger.debug("content: %s", str(content))
		cover_url = ""
		cover_title = ""
		events = content.get("events", [])
		for event in events:
			url = ""
			starttime = event.get("startTime", 0)
			date_raw = starttime.split('+')[0]
			timestart = int(time.mktime(datetime.strptime(date_raw, "%Y-%m-%dT%H:%M:%S").timetuple()))
			title = event.get("title", "n/a")
			channel = event.get("channel", "")
			if channel == channel_id:
				photo = event.get("photo", "")
				if photo:
					url = "https://tvfueralle.de" + photo["url"]
					logger.debug("image url: %s", url)

				if not self.findEvent(timestart, event_start, length):
					logger.debug(">>> saving: url: %s, title: %s", url, title)
					cover_url = url
					cover_title = title
				else:
					logger.debug(">>> break: url: %s, title: %s", cover_url, cover_title)
					break
		else:
			cover_url = ""
			cover_title = "n/a"
		logger.debug("cover_title: %s, cover_url: %s", cover_title, cover_url)
		return cover_url
