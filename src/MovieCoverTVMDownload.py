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


import json
import time
from datetime import datetime, timedelta
from Debug import logger
from MovieCoverUNIDownload import MovieCoverUNIDownload
from WebRequests import WebRequests


class MovieCoverTVMDownload(WebRequests, MovieCoverUNIDownload):

	def __init__(self):
		WebRequests.__init__(self)
		MovieCoverUNIDownload.__init__(self)

	def getCoverUrl(self, channel_id, event_start, length):
		content = []
		day = datetime.now() - timedelta(days=1)
		date_from = str(day.strftime("%Y-%m-%dT00:00:00"))
		day = datetime.now() + timedelta(days=1)
		date_to = str(day.strftime("%Y-%m-%dT00:00:00"))
		logger.debug("date_from: %s, date_to: %s", date_from, date_to)
		url = "http://capi.tvmovie.de/v1/broadcasts?fields=id,title,airTime,previewImage&channel=%s&date_from=%s&date_to=%s" % (channel_id, date_from, date_to)
		logger.debug("url: %s", url)
		r_content = self.getContent(url)
		if r_content and "errMsg" not in r_content:
			logger.debug("r_content: %s", r_content)
			content = json.loads(r_content)
			logger.debug("content: %s", content)
		url = self.parseEvents("", content, event_start, length)
		logger.debug("url: %s", url)
		return url

	def parseEvents(self, _channel_id, content, event_start, length):
		logger.info("...")
		logger.debug("content: %s", str(content))
		cover_url = ""
		cover_title = ""
		title = "n/a"
		if content and "channels" in content:
			for channel in content["channels"]:
				if "broadcasts" in channel:
					for event in channel["broadcasts"]:
						url = ""
						if "title" in event:
							title = event["title"]
						starttime = datetime.fromtimestamp(0)
						if "airTime" in event:
							starttime = event["airTime"]
							logger.debug("starttime: %s", starttime)
						timestart = int(time.mktime(datetime.strptime(starttime, "%Y-%m-%d %H:%M:%S").timetuple()))
						if "previewImage" in event:
							image = str(event["previewImage"]["id"])
							url = "https://images.tvmovie.de/760x430/North/%s" % image
							logger.debug("url: %s", url)

						if not self.findEvent(timestart, event_start, length):
							cover_url = url
							cover_title = title
						else:
							break
		logger.debug("cover_title: %s, cover_url: %s", cover_title, cover_url)
		return cover_url
