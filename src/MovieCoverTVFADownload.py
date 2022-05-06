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


import time
import json
from datetime import datetime
from Debug import logger
from MovieCoverUNIDownload import MovieCoverUNIDownload
from WebRequests import WebRequests


class MovieCoverTVFADownload(WebRequests, MovieCoverUNIDownload):

	def __init__(self):
		WebRequests.__init__(self)
		MovieCoverUNIDownload.__init__(self)

	def getCoverUrl(self, channel_id, event_start, length):
		content = []
		to_time = datetime.now().strftime("%Y-%m-%d")
		url = "https://tvfueralle.de/api/broadcasts/%s" % to_time
		logger.debug("url: %s", url)
		r_content = self.getContent(url)
		if r_content and "errMsg" not in r_content:
			#logger.debug("r_content: %s", r_content)
			content = json.loads(r_content)
			#logger.debug("content: %s", content)
		url = self.parseEvents(content, event_start, length, channel_id)
		logger.debug("url: %s", url)
		return url

	def parseEvents(self, content, event_start, length, channel_id):
		logger.info("...")
		#logger.debug("content: %s", str(content))
		cover_url = ""
		cover_title = ""
		title = "n/a"
		if content and "events" in content:
			for event in content["events"]:
				url = ""
				starttime = 0
				if "startTime" in event:
					starttime = event["startTime"]
				date_raw = starttime.split('+')[0]
				timestart = int(time.mktime(datetime.strptime(date_raw, "%Y-%m-%dT%H:%M:%S").timetuple()))
				if "title" in event:
					title = event["title"]

				if "channel" in event and event["channel"] == channel_id and "content" in event:
					if "photo" in event:
						url = "https://tvfueralle.de" + event["photo"]["url"]
						logger.debug("image url: %s", url)

					if not self.findEvent(timestart, event_start, length):
						cover_url = url
						cover_title = title
					else:
						break
		logger.debug("cover_title: %s, cover_url: %s", cover_title, cover_url)
		return cover_url
