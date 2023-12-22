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
from datetime import datetime, timedelta
from .Debug import logger
from .MovieCoverUNIDownload import MovieCoverUNIDownload
from .WebRequests import WebRequests


class MovieCoverTVMDownload(WebRequests, MovieCoverUNIDownload):

	def __init__(self):
		WebRequests.__init__(self)
		MovieCoverUNIDownload.__init__(self)

	def getCoverUrl(self, channel_id, _event_start):
		day = datetime.now() - timedelta(days=1)
		date_from = str(day.strftime("%Y-%m-%dT00:00:00"))
		day = datetime.now() + timedelta(days=1)
		date_to = str(day.strftime("%Y-%m-%dT00:00:00"))
		logger.debug("date_from: %s, date_to: %s", date_from, date_to)
		url = "http://capi.tvmovie.de/v1/broadcasts?fields=id,title,airTime,previewImage&channel=%s&date_from=%s&date_to=%s" % (channel_id, date_from, date_to)
		logger.debug("url: %s", url)
		return url, []

	def parseEvents(self, _channel_id, content, event_start, length):
		logger.info("event_start: %s", datetime.fromtimestamp(event_start))
		logger.debug("content: %s", str(content))
		cover_url = ""
		cover_title = "n/a"
		if content:
			channels = content.get("channels", [])
			for channel in channels:
				broadcasts = channel.get("broadcasts", [])
				for event in broadcasts:
					url = ""
					title = event.get("title", "")
					starttime = event.get("airTime", "")
					logger.debug(">>> starttime: %s", starttime)
					timestart = int(time.mktime(datetime.strptime(starttime, "%Y-%m-%d %H:%M:%S").timetuple()))
					if "previewImage" in event:
						image = str(event["previewImage"]["id"])
						if image:
							url = "https://images.tvmovie.de/760x430/North/%s" % image
						logger.debug("url: %s", url)

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
