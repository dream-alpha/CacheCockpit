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


import os
from Components.config import config
from Plugins.Plugin import PluginDescriptor
from .__init__ import _
from .Debug import logger
from .Version import VERSION
from .ConfigInit import ConfigInit
from .ConfigScreen import ConfigScreen
from .FileManager import FileManager
from .Trashcan import Trashcan
from .Recording import Recording
from .SkinUtils import loadPluginSkin


def openSettings(session, **__):
	logger.info("...")
	session.open(ConfigScreen, config.plugins.moviecockpit)


def enteringStandby(reason):
	logger.info("reason: %s, count: %d", reason, config.misc.standbyCounter.value)
	# if Screens.Standby.inStandby and config.misc.standbyCounter.value == 1 and config.plugins.cachecockpit.archive_enable.value:
	# 	Screens.Standby.inStandby.onClose.append(leavingStandby)


def leavingStandby():
	logger.info("...")
	# if config.misc.standbyCounter.value == 1 and config.plugins.cachecockpit.archive_enable.value:
	# 	logger.debug("cancelling %s jobs", len(jobs))
	# 	FileManager.getInstance().cancelJobs()


def autoStart(reason, **kwargs):
	if reason == 0:  # startup
		if "session" in kwargs:
			logger.info("+++ Version: %s starts...", VERSION)
			logger.info("reason: %s", reason)
			# session = kwargs["session"]
			Recording()
			Trashcan.getInstance()
			loadPluginSkin("skin.xml")
	elif reason == 1:  # shutdown
		logger.info("--- shutdown")
		if not os.path.exists("/etc/enigma2/.cachecockpit"):
			FileManager.getInstance().closeDatabase()
	else:
		logger.info("reason not handled: %s", reason)


def Plugins(**__):
	logger.info("+++ Plugins")
	ConfigInit()

	config.misc.standbyCounter.addNotifier(enteringStandby, initial_call=False)

	descriptors = []
	descriptors.append(
		PluginDescriptor(
			where=[
				PluginDescriptor.WHERE_SESSIONSTART,
				PluginDescriptor.WHERE_AUTOSTART
			],
			fnc=autoStart
		)
	)

	descriptors.append(
		PluginDescriptor(
			name="CacheCockpit" + " - " + _("Setup"),
			description=_("Open setup"),
			icon="CacheCockpit.svg",
			where=[
				PluginDescriptor.WHERE_PLUGINMENU,
			],
			fnc=openSettings
		)
	)

	return descriptors
