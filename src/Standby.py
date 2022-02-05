#!/usr/bin/python
from __init__ import _
from Screens.Screen import Screen
from enigma import quitMainloop, iRecordableService, eTimer
from Screens.MessageBox import MessageBox
from time import time
from Components.Task import job_manager
import Screens.Standby


class TryQuitMainloop(MessageBox):
	def __init__(self, session, retval=1, timeout=-1, default_yes=True):
		self.session = session
		self.retval = retval
		self.poll_actions_timer = eTimer()
		self.poll_actions_timer_conn = self.poll_actions_timer.timeout.connect(self.pollActions)
		self.question = ""
		reason = ""

		reason = self.checkActions()
		if not reason and retval == 16:
			reason = _("You won't be able to leave Recovery Mode without physical access to the device!")
		if reason:
			if retval == 1:
				self.question = _("Really shutdown now?")
			elif retval == 2:
				self.question = _("Really reboot now?")
			elif retval == 4:
				pass
			elif retval == 16:
				self.question = _("Really reboot into Recovery Mode?")
			else:
				self.question = _("Really restart now?")

			if self.question:
				reason += "\n\n" + self.question
				MessageBox.__init__(self, session, reason, type=MessageBox.TYPE_YESNO, timeout=timeout, default=default_yes)
				self.skinName = "MessageBox"

			session.nav.record_event.append(self.getRecordEvent)
			self.onShow.append(self.__onShow)
			self.onHide.append(self.__onHide)
		else:
			self.skin = """<screen name="TryQuitMainloop" position="0,0" size="0,0" flags="wfNoBorder"/>"""
			Screen.__init__(self, session)
			self.close(True)

	def checkJobs(self):
		reason = ""
		jobs = len(job_manager.getPendingJobs())
		if jobs:
			self.poll_actions_timer.start(5 * 1000, True)
			if jobs == 1:
				job = job_manager.getPendingJobs()[0]
				reason = "%s: %s\n%s (%d%%)" % (job.getStatustext(), _("File operation"), job.name, int(100 * job.progress / float(job.end)))
			else:
				reason = "%d " % jobs + _("jobs are running in the background!")
			if hasattr(self, "text"):
				self["text"].setText(reason + "\n\n" + self.question)
		return reason

	def checkTimers(self):
		reason = ""
		next_rec_time = -1
		recordings = self.session.nav.getRecordings()
		next_rec_time = self.session.nav.RecordTimer.getNextRecordingTime()
		if recordings or (next_rec_time > 0 and (next_rec_time - time()) < 360):
			self.poll_actions_timer.start(360 * 1000, True)
			reason = _("Recording(s) are in progress or starting soon!")
			if hasattr(self, "text"):
				self["text"].setText(reason + "\n\n" + self.question)
		return reason

	def checkActions(self):
		reason = self.checkJobs()
		if not reason:
			reason = self.checkTimers()
		return reason

	def pollActions(self):
		if not self.checkActions():
			self.close(True)

	def getRecordEvent(self, _recservice, event):
		if event == iRecordableService.evEnd:
			self.pollActions()
		elif event == iRecordableService.evStart:
			self.poll_actions_timer.stop()

	def close(self, value):
		if self.getRecordEvent in self.session.nav.record_event:
			self.session.nav.record_event.remove(self.getRecordEvent)
		if value:
			self.poll_actions_timer.stop()
			for job in job_manager.getPendingJobs():
				job.abort()
			quitMainloop(self.retval)
		else:
			MessageBox.close(self, True)

	def __onShow(self):
		Screens.Standby.inTryQuitMainloop = True

	def __onHide(self):
		Screens.Standby.inTryQuitMainloop = False
