#!/usr/bin/python
from __init__ import _
from Screens.Screen import Screen
from enigma import quitMainloop, iRecordableService, eTimer
from Screens.MessageBox import MessageBox
from time import time
from Components.Task import job_manager
import Screens.Standby


class TryQuitMainloop(MessageBox):
	def __init__(self, session, retvalue=1, timeout=-1, default_yes=True):
		self.session = session
		self.retval = retvalue
		self.check_jobs_timer = eTimer()
		self.check_jobs_timer_conn = self.check_jobs_timer.timeout.connect(self.updateJobs)
		self.connected = False
		self.question = ""

		reason = self.checkJobs()
		if reason:
			self.check_jobs_timer.start(5000, True)
		else:
			reason = self.checkTimers()

		if retvalue == 16:
			reason = _("Really reboot into Recovery Mode?\n")
		if reason:
			if retvalue == 1:
				self.question = _("Really shutdown now?")
				reason += self.question
				MessageBox.__init__(self, session, reason, type=MessageBox.TYPE_YESNO, timeout=timeout, default=default_yes)
			elif retvalue == 2:
				self.question = _("Really reboot now?")
				reason += self.question
				MessageBox.__init__(self, session, reason, type=MessageBox.TYPE_YESNO, timeout=timeout, default=default_yes)
			elif retvalue == 4:
				pass
			elif retvalue == 16:
				self.question = _("You won't be able to leave Recovery Mode without physical access to the device!")
				reason += self.question
				MessageBox.__init__(self, session, reason, type=MessageBox.TYPE_YESNO, timeout=timeout, default=default_yes)
			else:
				self.question = _("Really restart now?")
				reason += self.question
				MessageBox.__init__(self, session, reason, type=MessageBox.TYPE_YESNO, timeout=timeout, default=default_yes)
			self.skinName = "MessageBox"
			session.nav.record_event.append(self.getRecordEvent)
			self.connected = True
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
			if jobs == 1:
				job = job_manager.getPendingJobs()[0]
				reason += "%s: %s (%d%%)\n" % (job.getStatustext(), job.name, int(100 * job.progress / float(job.end)))
			else:
				reason += "%d " % jobs + _("jobs are running in the background!") + "\n"
		return reason

	def checkTimers(self):
			reason = ""
			next_rec_time = -1
			recordings = self.session.nav.getRecordings()
			if not recordings:
				next_rec_time = self.session.nav.RecordTimer.getNextRecordingTime()
			if recordings or (next_rec_time > 0 and (next_rec_time - time()) < 360):
				reason = _("Recording(s) are in progress or coming up in few seconds!") + '\n'
			return reason

	def updateJobs(self):
		reason = self.checkJobs()
		if reason:
			self["text"].setText(reason + self.question)
			self.check_jobs_timer.start(5000, True)
		else:
			reason = self.checkTimers()
			if reason:
				self["text"].setText(reason + self.question)
				self.session.nav.record_event.append(self.getRecordEvent)
			else:
				self.skin = """<screen name="TryQuitMainloop" position="0,0" size="0,0" flags="wfNoBorder"/>"""
				Screen.__init__(self, self.session)
				self.close(True)

	def getRecordEvent(self, _recservice, event):
		if event == iRecordableService.evEnd:
			recordings = self.session.nav.getRecordings()
			if not recordings: # no more recordings exist
				rec_time = self.session.nav.RecordTimer.getNextRecordingTime()
				if rec_time > 0 and (rec_time - time()) < 360:
					self.initTimeout(360) # wait for next starting timer
					self.startTimer()
				else:
					self.close(True) # immediate shutdown
		elif event == iRecordableService.evStart:
			self.stopTimer()

	def close(self, value):
		if self.connected:
			self.connected = False
			self.session.nav.record_event.remove(self.getRecordEvent)
		if value:
			self.check_jobs_timer.stop()
			for job in job_manager.getPendingJobs():
				job.abort()
			quitMainloop(self.retval)
		else:
			MessageBox.close(self, True)

	def __onShow(self):
		Screens.Standby.inTryQuitMainloop = True

	def __onHide(self):
		Screens.Standby.inTryQuitMainloop = False
