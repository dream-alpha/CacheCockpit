#!/usr/bin/pyhon
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


from Components.config import config, ConfigDirectory, ConfigSelection, ConfigYesNo, ConfigSubsection, ConfigNothing, NoSave
from .Debug import logger, log_levels


class ConfigInit():

	def __init__(self):
		logger.info("...")
		config.plugins.cachecockpit = ConfigSubsection()
		config.plugins.cachecockpit.fake_entry = NoSave(ConfigNothing())
		config.plugins.cachecockpit.archive_enable = ConfigYesNo(default=False)
		config.plugins.cachecockpit.archive_source_dir = ConfigDirectory(default="/media/hdd/movie")
		config.plugins.cachecockpit.archive_target_dir = ConfigDirectory(default="/media/hdd/movie")
		config.plugins.cachecockpit.debug_log_path = ConfigDirectory(default="/media/hdd")
		config.plugins.cachecockpit.debug_log_level = ConfigSelection(default="INFO", choices=list(log_levels.keys()))
