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


from Components.config import config
from Plugins.SystemPlugins.SocketCockpit.RequestClient import RequestClient
from Plugins.SystemPlugins.SocketCockpit.OnlineMonitor import OnlineMonitor


class SourceSelector():

	def __init__(self, csel):
		self.csel = csel
		self.online_monitor = OnlineMonitor.getInstance()

	def sendRequest(self, request):
		request_client_thread = RequestClient(config.plugins.socketcockpit.server_ip_address.value, config.plugins.socketcockpit.request_server_port.value, request)
		request_client_thread.start()
		request_client_thread.join()
		return request_client_thread.reply

	def getFileList(self, dirs, top_level, recursively=False):
		file_list = self.csel.getFileList(dirs, recursively)
		if config.plugins.socketcockpit.client.value and self.online_monitor.isOnline():
			if top_level:
				dirs = []
			file_list2 = self.sendRequest("multiple:FileManager().getFileList(%s, %s)" % (dirs, recursively))
			if file_list2:
				file_list += file_list2
		return file_list

	def getLogFileList(self, dirs, top_level):
		file_list = self.csel.getLogFileList(dirs)
		if config.plugins.socketcockpit.client.value and self.online_monitor.isOnline():
			if top_level:
				dirs = []
			file_list2 = self.sendRequest("multiple:FileManager().getLogFileList(%s)" % dirs)
			if file_list2:
				file_list += file_list2
		return file_list

	def getDirList(self, dirs, top_level):
		file_list = self.csel.getDirList(dirs)
		if config.plugins.socketcockpit.client.value and self.online_monitor.isOnline():
			if top_level:
				dirs = []
			file_list2 = self.sendRequest("multiple:FileManager().getDirList(%s)" % dirs)
			if file_list2:
				file_list += file_list2
		return file_list

	def getFile(self, table, path):
		afile = self.csel.getFile(table, path)
		if not afile and config.plugins.socketcockpit.client.value and self.online_monitor.isOnline():
			afile = self.sendRequest("single:FileManager().getFile('''%s''', '''%s''')" % (table, path))
		return afile

	def getCountSize(self, path):
		count, size = self.csel.getCountSize(path)
		if config.plugins.socketcockpit.client.value and self.online_monitor.isOnline():
			response = self.sendRequest("single:FileManager().getCountSize('''%s''')" % path)
			if response:
				count2, size2 = response
				count += count2
				size += size2
		return count, size

	def getLockList(self):
		lock_list = self.csel.getLockList()
		if config.plugins.socketcockpit.client.value and self.online_monitor.isOnline():
			lock_list2 = self.sendRequest("single:FileManager().getLockList()")
			if lock_list2:
				lock_list.update(lock_list2)
		return lock_list

	def getRecordings(self):
		recordings_list = self.csel.getRecordings()
		if config.plugins.socketcockpit.client.value and self.online_monitor.isOnline():
			recordings_list2 = self.sendRequest("single:FileManager().getRecordings()")
			if recordings_list2:
				recordings_list += recordings_list2
		return recordings_list
