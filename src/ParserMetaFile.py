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
from Debug import logger
from FileUtils import readFile, writeFile


class ParserMetaFile():

	meta_keys = [
		"service_reference", "name", "description", "rec_time", "tags", "length", "size", "service_data"
	]

	xmeta_keys = [
		"timer_start_time", "timer_stop_time", "recording_start_time", "recording_stop_time",
		"recording_margin_before", "recording_margin_after", "datestring", "timestring",
		"timestart", "year", "broadcaster", "title", "genre", "fsk",
		"season", "episode_number", "episode_title", "rating"
	]

	meta_ints = [
		"rec_time", "length", "size", "timer_start_time", "timer_stop_time", "recording_start_time",
		"recording_stop_time", "recording_margin_before", "recording_margin_after", "timestart"
	]

	def __init__(self, path):
		self.path = path
		self.meta_path = path + ".meta"
		self.xmeta_path = path + ".xmeta"
		if not os.path.exists(self.meta_path):
			path, ext = os.path.splitext(path)
			# remove cut number
			if path[-4] == "_" and path[-3:].isdigit():
				path = path[:-4] + ext
				self.meta_path = path + ".meta"
				self.xmeta_path = path + ".xmeta"

		self.meta_list = self.readMeta(self.meta_path)
		self.meta = self.list2dict(self.meta_list, self.meta_keys)

		self.xmeta_list = self.readMeta(self.xmeta_path)
		while len(self.xmeta_list) <= len(self.xmeta_keys):
			self.xmeta_list.append("")
		self.xmeta = self.list2dict(self.xmeta_list, self.xmeta_keys)

	def list2dict(self, alist, keys):
		adict = {}
		for i, key in enumerate(keys):
			if key in self.meta_ints:
				if alist[i]:
					adict[key] = int(alist[i])
				else:
					adict[key] = 0
			else:
				adict[key] = alist[i]
		return adict

	def dict2list(self, adict, keys):
		alist = []
		for i, key in enumerate(keys):
			alist[i] = adict[key]

	def readMeta(self, path):
		meta_list = readFile(path).splitlines()
		meta_list = [list_item.strip() for list_item in meta_list]
		return meta_list

	def getMeta(self):
		self.meta.update(self.xmeta)
		logger.debug("meta: %s", self.meta)
		return self.meta

	def updateXMeta(self, xmeta):
		logger.debug("xmeta: %s", xmeta)
		for key in xmeta:
			self.xmeta_list[self.xmeta_keys.index(key)] = xmeta[key]
		self.saveXMeta()

	def saveXMeta(self):
		data = ""
		for line in self.xmeta_list:
			data += "%s\n" % line
		writeFile(self.xmeta_path, data)
