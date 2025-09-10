#!/usr/bin/python
# coding=utf-8
#
# Copyright (C) 2018-2025 by dream-alpha
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
from .Debug import logger
from .Version import VERSION
from .ConfigInit import ConfigInit
from .FileManager import FileManager
from .Recording import Recording
from .FileManagerUtils import SQL_DB_MVC, SQL_DB_MDC
from .FileUtils import createDirectory


def enteringStandby(_reason):
    logger.info("count: %d", config.misc.standbyCounter.value)
    # if Screens.Standby.inStandby and config.misc.standbyCounter.value == 1 and config.plugins.moviecockpit.archive_enable.value:
    # 	Screens.Standby.inStandby.onClose.append(leavingStandby)


def leavingStandby():
    logger.info("...")
    # if config.misc.standbyCounter.value == 1 and config.plugins.moviecockpit.archive_enable.value:
    # 	logger.debug("cancelling %s jobs", len(jobs))
    # 	FileManager.getInstance("MVC").cancelJobs()


def autoStart(reason, **kwargs):
    if reason == 0:  # startup
        if "session" in kwargs:
            logger.info("+++ Version: %s starts...", VERSION)
            # session = kwargs["session"]
            try:
                if not os.path.exists(config.plugins.mediacockpit.database_directory.value):
                    createDirectory(
                        config.plugins.mediacockpit.database_directory.value)
            except Exception:
                logger.debug("MediaCockpit plugin is not installed.")
            try:
                if not os.path.exists(config.plugins.moviecockpit.database_directory.value):
                    createDirectory(
                        config.plugins.moviecockpit.database_directory.value)
            except Exception:
                logger.debug("MovieCockpit plugin is not installed.")
            if os.path.exists(os.path.join(config.plugins.moviecockpit.database_directory.value, "." + SQL_DB_MVC)) or not os.path.exists(os.path.join(config.plugins.moviecockpit.database_directory.value, SQL_DB_MVC)):
                FileManager.getInstance("MVC")
            Recording.getInstance()
    elif reason == 1:  # shutdown
        logger.info("--- shutdown")
        try:
            moviecockpit_database = os.path.join(
                config.plugins.moviecockpit.database_directory.value, SQL_DB_MVC)
            if os.path.exists(moviecockpit_database):
                FileManager.getInstance("MVC").closeDatabase()
        except Exception:
            logger.debug("MovieCockpit plugin is not installed.")

        try:
            mediacockpit_database = os.path.join(
                config.plugins.mediacockpit.database_directory.value, SQL_DB_MDC)
            if os.path.exists(mediacockpit_database):
                FileManager.getInstance("MDC").closeDatabase()
        except Exception:
            logger.debug("MediaCockpit plugin is not installed.")


def Plugins(**__):
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

    return descriptors
