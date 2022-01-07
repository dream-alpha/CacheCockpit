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
from enigma import eServiceReference


SID_DVB = eServiceReference.idDVB	# eServiceFactoryDVB::id  enum{id = 0x0001};
SID_DVD = eServiceReference.idDVD	# eServiceFactoryDVD::id  enum{id = 0x1111};
SID_M2TS = eServiceReference.idM2TS	# eServiceFactoryM2TS::id enum{id = 0x0003};
SID_GST = eServiceReference.idGST	# eServiceFactoryGST::id  enum{id = 0x1001};


EXT_TS = frozenset([".ts", ".trp"])
EXT_M2TS = frozenset([".m2ts"])
EXT_DVD = frozenset([".ifo", ".iso", ".img"])
EXT_VIDEO = frozenset([".ts", ".trp", ".avi", ".divx", ".f4v", ".flv", ".img", ".ifo", ".iso", ".m2ts", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".mts", ".vob", ".wmv", ".bdmv", ".asf", ".stream", ".webm"])
EXT_BLU = frozenset([".bdmv"])


ALL_VIDEO = [".avi", ".ts", ".trp", ".divx", ".f4v", ".img", ".ifo", ".iso", ".m4v", ".mkv", ".mov", ".mp4", ".mpeg", ".mpg", ".mts", ".vob", ".wmv", ".bdmv", ".asf", ".stream", ".webm"]
ALL_PICTURE = [".jpg", ".jpeg", ".png"]
ALL_MUSIC = [".mp3", ".wma"]
ALL_PLAYLIST = [".m3u"]
ALL_MEDIA = ALL_VIDEO + ALL_PICTURE + ALL_MUSIC + ALL_PLAYLIST


DEFAULT_VIDEO_PID = 0x44
DEFAULT_AUDIO_PID = 0x45


def getService(path, name=""):
	service = None
	ext = os.path.splitext(path)[1].lower()
	if ext in EXT_TS:
		service = eServiceReference(SID_DVB, 0, path)
	elif ext in EXT_DVD:
		service = eServiceReference(SID_DVD, 0, path)
	elif ext in EXT_M2TS:
		service = eServiceReference(SID_M2TS, 0, path)
	else:
		service = eServiceReference(SID_GST, 0, path)
		service.setData(0, DEFAULT_VIDEO_PID)
		service.setData(1, DEFAULT_AUDIO_PID)
	service.setName(name)
	return service
