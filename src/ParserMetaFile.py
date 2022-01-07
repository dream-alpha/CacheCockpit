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


import os
from FileUtils import readFile, writeFile
from Components.config import config
from CutListUtils import ptsToSeconds


META_IDX_SERVICE = 0
META_IDX_NAME = 1
META_IDX_DESC = 2
META_IDX_RECTIME = 3
META_IDX_TAGS = 4
META_IDX_LENGTH = 5
META_IDX_FILESIZE = 6
META_IDX_SERVICEDATA = 7


XMETA_IDX_STARTRECTIME = 0
XMETA_IDX_STOPRECTIME = 1
XMETA_IDX_STARTTIMERTIME = 2
XMETA_IDX_STOPTIMERTIME = 3
XMETA_IDX_MARGINBEFORE = 4
XMETA_IDX_MARGINAFTER = 5


class ParserMetaFile():

	def __init__(self, path):
		self.path = path
		self.meta_path = path + ".meta"
		self.xmeta_path = path + ".xmeta"
		if not os.path.exists(self.meta_path):
			path, ext = os.path.splitext(path)
			# remove cut number
			if path[-4:-3] == "_" and path[-3:].isdigit():
				path = path[:-4] + ext
				self.meta_path = path + ".meta"
				self.xmeta_path = path + ".xmeta"
		self.meta_list = self.readMeta(self.meta_path)
		while len(self.meta_list) <= META_IDX_SERVICEDATA:
			self.meta_list.append("")
		if not self.meta_list[META_IDX_RECTIME]:
			self.meta_list[META_IDX_RECTIME] = int(os.stat(self.path).st_ctime)
		if not self.meta_list[META_IDX_LENGTH]:
			self.meta_list[META_IDX_LENGTH] = 0
		else:
			self.meta_list[META_IDX_LENGTH] = ptsToSeconds(int(self.meta_list[META_IDX_LENGTH]))
		if not self.meta_list[META_IDX_FILESIZE]:
			self.meta_list[META_IDX_FILESIZE] = int(os.path.getsize(self.path))

		self.xmeta_list = self.readMeta(self.xmeta_path)
		while len(self.xmeta_list) <= XMETA_IDX_MARGINAFTER:
			self.xmeta_list.append("")
		if not self.xmeta_list[XMETA_IDX_STARTTIMERTIME]:
			self.xmeta_list[XMETA_IDX_STARTTIMERTIME] = 0
		if not self.xmeta_list[XMETA_IDX_STOPTIMERTIME]:
			self.xmeta_list[XMETA_IDX_STOPTIMERTIME] = 0
		if not self.xmeta_list[XMETA_IDX_STARTRECTIME]:
			self.xmeta_list[XMETA_IDX_STARTRECTIME] = int(self.meta_list[META_IDX_RECTIME])
		if not self.xmeta_list[XMETA_IDX_STOPRECTIME]:
			self.xmeta_list[XMETA_IDX_STOPRECTIME] = 0
		if not self.xmeta_list[XMETA_IDX_MARGINBEFORE]:
			self.xmeta_list[XMETA_IDX_MARGINBEFORE] = config.recording.margin_before.value * 60
		if not self.xmeta_list[XMETA_IDX_MARGINAFTER]:
			self.xmeta_list[XMETA_IDX_MARGINAFTER] = config.recording.margin_after.value * 60

	def readMeta(self, path):
		meta_list = readFile(path).splitlines()
		meta_list = [list_item.strip() for list_item in meta_list]
		return meta_list

	def getMeta(self):
		meta = self.getMetaData()
		meta.update(self.getXMetaData())
		return meta

	def getMetaData(self):
		meta = {}
		if self.meta_list and len(self.meta_list) > META_IDX_SERVICEDATA:
			meta["service_reference"] = self.meta_list[META_IDX_SERVICE]
			meta["name"] = self.meta_list[META_IDX_NAME]
			meta["description"] = self.meta_list[META_IDX_DESC]
			meta["rec_time"] = int(self.meta_list[META_IDX_RECTIME])
			meta["tags"] = self.meta_list[META_IDX_TAGS]
			meta["length"] = int(self.meta_list[META_IDX_LENGTH])
			meta["size"] = int(self.meta_list[META_IDX_FILESIZE])
			meta["service_data"] = self.meta_list[META_IDX_SERVICEDATA]
		return meta

	def getXMetaData(self):
		meta = {}
		if self.xmeta_list and len(self.xmeta_list) > XMETA_IDX_STOPRECTIME:
			meta["timer_start_time"] = int(self.xmeta_list[XMETA_IDX_STARTTIMERTIME])
			meta["timer_stop_time"] = int(self.xmeta_list[XMETA_IDX_STOPTIMERTIME])
			meta["recording_start_time"] = int(self.xmeta_list[XMETA_IDX_STARTRECTIME])
			meta["recording_stop_time"] = int(self.xmeta_list[XMETA_IDX_STOPRECTIME])
			meta["recording_margin_before"] = int(self.xmeta_list[XMETA_IDX_MARGINBEFORE])
			meta["recording_margin_after"] = int(self.xmeta_list[XMETA_IDX_MARGINAFTER])
		return meta

	def updateXMeta(self, xmeta):
		for tag in xmeta:
			if tag == "timer_start_time":
				self.xmeta_list[XMETA_IDX_STARTTIMERTIME] = xmeta["timer_start_time"]
			if tag == "timer_stop_time":
				self.xmeta_list[XMETA_IDX_STOPTIMERTIME] = xmeta["timer_stop_time"]
			if tag == "recording_start_time":
				self.xmeta_list[XMETA_IDX_STARTRECTIME] = xmeta["recording_start_time"]
			if tag == "recording_stop_time":
				self.xmeta_list[XMETA_IDX_STOPRECTIME] = xmeta["recording_stop_time"]
			if tag == "recording_margin_before":
				self.xmeta_list[XMETA_IDX_MARGINBEFORE] = xmeta["recording_margin_before"]
			if tag == "recording_margin_after":
				self.xmeta_list[XMETA_IDX_MARGINAFTER] = xmeta["recording_margin_after"]
		self.saveXMeta()

	def saveXMeta(self):
		data = ""
		for line in self.xmeta_list:
			data += "%s\n" % line
		writeFile(self.xmeta_path, data)
