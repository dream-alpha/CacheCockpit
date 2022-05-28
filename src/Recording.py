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
import time
from Debug import logger
from enigma import quitMainloop
from Components.config import config
import NavigationInstance
from timer import TimerEntry
from DelayTimer import DelayTimer
from ParserMetaFile import ParserMetaFile
from FileManager import FileManager
from FileManagerUtils import FILE_OP_MOVE, FILE_IDX_NAME, FILE_IDX_EVENT_START_TIME, FILE_IDX_LENGTH
import Screens.Standby
from RecordTimer import AFTEREVENT
from MovieCoverDownload import MovieCoverDownload


class Recording():

	def __init__(self):
		logger.info("...")
		self.after_events = []
		NavigationInstance.instance.RecordTimer.on_state_change.append(self.recordingEvent)
		self.check4ActiveRecordings()
		if config.plugins.moviecockpit.timer_autoclean.value:
			NavigationInstance.instance.RecordTimer.cleanup()

	def updateXMetaFile(self, timer):
		ParserMetaFile(timer.Filename).updateXMeta({
			"recording_start_time": int(time.time()),
			"recording_stop_time": 0,
			"timer_start_time": timer.begin,
			"timer_stop_time": timer.end,
			"recording_margin_before": config.recording.margin_before.value * 60,
			"recording_margin_after": config.recording.margin_after.value * 60,
		})

	def recordingEvent(self, timer):
		TIMER_STATES = ["StateWaiting", "StatePrepared", "StateRunning", "StateEnded"]
		if timer and not timer.justplay and not hasattr(timer, "timeshift"):
			logger.debug(
				"timer.Filename: %s, timer.state: %s",
				timer.Filename, (TIMER_STATES[timer.state] if timer.state in range(0, len(TIMER_STATES)) else timer.state)
			)

			if timer.state == TimerEntry.StateRunning:
				logger.debug("REC START for: %s, afterEvent: %s", timer.Filename, timer.afterEvent)
				if Screens.Standby.inStandby and config.misc.standbyCounter.value == 1 and config.plugins.cachecockpit.archive_enable.value:
					config.misc.isNextRecordTimerAfterEventActionAuto.value = False
					config.misc.isNextRecordTimerAfterEventActionAuto.save()
					self.after_events.append(timer.afterEvent)
					timer.afterEvent1 = timer.afterEvent
					timer.afterEvent = AFTEREVENT.NONE
				self.updateXMetaFile(timer)
				DelayTimer(250, FileManager.getInstance().loadDatabaseFile, timer.Filename)
				if config.plugins.moviecockpit.cover_auto_download.value:
					DelayTimer(1000, self.autoCoverDownload, timer.Filename, timer.service_ref)

			elif timer.state in [TimerEntry.StateEnded, TimerEntry.StateWaiting]:
				logger.debug("REC END for: %s, afterEvent: %s", timer.Filename, timer.afterEvent)
				if os.path.exists(timer.Filename):
					ParserMetaFile(timer.Filename).updateXMeta({"recording_stop_time": int(time.time())})
					FileManager.getInstance().loadDatabaseFile(timer.Filename)
					if Screens.Standby.inStandby and config.misc.standbyCounter.value == 1 and config.plugins.cachecockpit.archive_enable.value:
						if hasattr(timer, "afterEvent1"):
							timer.afterEvent = timer.afterEvent1
						FileManager.getInstance().execFileManagerOp(FILE_OP_MOVE, timer.Filename, config.plugins.cachecockpit.archive_target_dir.value, self.handleAfterEvent)

	def handleAfterEvent(self, _file_op, _path, _target_dir, _error):
		logger.debug("...")
		jobs = len(FileManager.getInstance().getPendingJobs())
		if jobs <= 1:
			do_shutdown = False
			for after_event in self.after_events:
				if after_event in [AFTEREVENT.AUTO, AFTEREVENT.DEEPSTANDBY]:
					do_shutdown = True
					break
			if do_shutdown:
				recordings = NavigationInstance.instance.getRecordings()
				if not recordings:
					rec_time = NavigationInstance.instance.RecordTimer.getNextRecordingTime()
					if rec_time > 0 and (rec_time - time.time()) < 360:
						logger.info("another recording starts in %s seconds, do not shut down yet", rec_time - time.time())
					else:
						logger.info("no starting recordings in the next 360 seconds, so we can shutdown")
						quitMainloop(8)
		else:
			logger.info("%d jobs still running", jobs)

	def check4ActiveRecordings(self):
		logger.debug("...")
		for timer in NavigationInstance.instance.RecordTimer.timer_list:
			if timer.Filename and timer.isRunning() and not timer.justplay:
				if not FileManager.getInstance().exists(timer.Filename):
					logger.debug("loadDatabaseFile: %s", timer.Filename)
					self.updateXMetaFile(timer)
					FileManager.getInstance().loadDatabaseFile(timer.Filename)

	def autoCoverDownload(self, path, service_ref):
		afile = FileManager.getInstance().getFile("recordings", path)
		if afile is not None:
			MovieCoverDownload().getMovieCover(
				path,
				service_ref,
				afile[FILE_IDX_NAME],
				afile[FILE_IDX_EVENT_START_TIME],
				afile[FILE_IDX_LENGTH],
			)
			FileManager.getInstance().loadDatabaseCover(path)
