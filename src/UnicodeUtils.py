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


from Debug import logger


def convertToUtf8(text, codepage="cp1252", first=True):
	if text and codepage is not None:
		try:
			if codepage != 'utf-8':
				text = text.decode(codepage).encode("utf-8")
			else:
				text.decode('utf-8')
		except (UnicodeDecodeError, AttributeError) as e:
			if first:
				text = convertToUtf8(text, "iso-8859-1", False)
			else:
				logger.error("text: %s, codepage: %s, first: %s, exception: %s", text, codepage, first, e)
	return text.strip()
