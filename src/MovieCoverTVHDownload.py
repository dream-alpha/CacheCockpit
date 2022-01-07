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


import json
from .Debug import logger
from .MovieCoverUNIDownload import MovieCoverUNIDownload
from .WebRequests import WebRequests


class MovieCoverTVHDownload(WebRequests, MovieCoverUNIDownload):

	def __init__(self):
		WebRequests.__init__(self)
		MovieCoverUNIDownload.__init__(self)

	def getCoverUrl(self, channel_id, event_start, length):
		content = []
		url = "http://mobile.hoerzu.de/programbystation"
		logger.debug("url: %s", url)
		r_content = self.getContent(url)
		if r_content and "errMsg" not in r_content:
			# logger.debug("r_content: %s", r_content)
			content = json.loads(r_content)
			# logger.debug("content: %s", content)
		url = self.parseEvents(content, event_start, length, channel_id)
		logger.debug("url: %s", url)
		return url

	def parseEvents(self, content, event_start, length, channel_id):
		logger.info("...")
		# logger.debug("content: %s", str(content))
		cover_url = ""
		cover_title = ""
		title = "n/a"
		if content:
			for events in content:
				if str(events["id"]) == channel_id:
					if "broadcasts" in events:
						for event in events["broadcasts"]:
							url = ""
							if "title" in event:
								title = event["title"]
							if "startTime" in event:
								timestart = event["startTime"]
							if "pic" in event:
								url = event["pic"]

							if not self.findEvent(timestart, event_start, length):
								cover_url = url
								cover_title = title
							else:
								break
		logger.debug("cover_title: %s, cover_url: %s", cover_title, cover_url)
		return cover_url
