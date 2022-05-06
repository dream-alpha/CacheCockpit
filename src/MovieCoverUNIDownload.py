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
from datetime import datetime
from Debug import logger
from Tools.Directories import resolveFilename, SCOPE_PLUGINS
from FileUtils import readFile


class MovieCoverUNIDownload():

	def __init__(self):
		return

	def getChannelId(self, channel_id_name, service_ref):
		logger.info("service_ref: %s", service_ref)
		channel_id = ""
		data = readFile(resolveFilename(SCOPE_PLUGINS, "SystemPlugins/CacheCockpit/tv_channels.json"))
		channels = json.loads(data)
		for channel in channels:
			if channel["servicehd"] == str(service_ref) or channel["servicesd"] == str(service_ref):
				if channel_id_name in channel:
					channel_id = channel[channel_id_name]
				break
		logger.debug("%s: %s", channel_id_name, channel_id)
		return channel_id

	def getCoverUrl(self, _channel_id, _event_start, _length):
		logger.error("should be overridden in child class")
		return ""

	def findEvent(self, timestart, event_start, length):
		logger.info("timestart: %s, event_start: %s", datetime.fromtimestamp(timestart), datetime.fromtimestamp(event_start))
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
			cover_url = self.getCoverUrl(channel_id, event_start, length)
		return cover_url
