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
from pipes import quote
from .Debug import logger


def getFfprobeDuration(path):
    logger.info("path: %s", path)
    try:
        duration = os.popen("ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 %s" % quote(path)).read()
        logger.debug("duration: %s", duration)
        duration = int(float(duration.replace("\n", "")))
    except Exception as e:
        logger.error("exception: %s", e)
        duration = 0
    return duration
