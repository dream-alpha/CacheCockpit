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


import json
from datetime import datetime
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from .Debug import logger
from .FileUtils import readFile


class MovieCoverUNIDownload():

	def __init__(self):
		return

	def getChannelId(self, channel_id_name, service_ref):
		logger.info("service_ref: %s", service_ref)
		sref = str(service_ref).split(":")[0 : 10]
		sref[1] = "0"
		service_ref = ":".join(sref) + ":"
		logger.info("service_ref: %s", service_ref)
		channel_id = ""
		data = readFile(resolveFilename(SCOPE_PLUGINS, "SystemPlugins/CacheCockpit/tv_channels.json"))
		channels = json.loads(data)
		for channel in channels:
			if service_ref in channel["services"]:
				if channel_id_name in channel:
					channel_id = channel[channel_id_name]
				break
		logger.debug("%s: %s", channel_id_name, channel_id)
		return channel_id

	def getCoverUrl(self, _channel_id, _event_start):
		logger.error("should be overridden in child class")
		return ""

	def getCoverContent(self, channel_id, event_start):
		content = []
		url, params = self.getCoverUrl(channel_id, event_start)
		r_content = self.getContent(url, params)
		if r_content and "errMsg" not in r_content:
			logger.debug("r_content: %s", r_content)
			content = json.loads(r_content)
			logger.debug("content: %s", content)
		return content

	def findEvent(self, timestart, event_start, length):
		logger.info("timestart: %s, timestart: %s, event_start: %s", timestart, datetime.fromtimestamp(timestart), datetime.fromtimestamp(event_start))
		middle = event_start + length / 2
		logger.debug("timestart: %s, middle: %s", datetime.fromtimestamp(timestart), datetime.fromtimestamp(middle))
		return timestart > middle

	def parseEvents(self, _channel_id, _content, _event_start, _length):
		logger.error("should be overridden in child class")
		return ""

	def getSourceMovieCover(self, path, cover_source, service_ref, title="", event_start=0, length=0):
		logger.info("path: %s, cover_source: %s, title: %s", path, cover_source, title)
		cover_url = ""
		channel_id = self.getChannelId(cover_source, service_ref)
		if channel_id:
			content = self.getCoverContent(channel_id, event_start)
			if content:
				cover_url = self.parseEvents(channel_id, content, event_start, length)
		logger.debug("cover_url: %s", cover_url)
		return cover_url
