import time
import socket
import os

from .. import simulator
import subprocess, signal

class GenericSimulator(simulator.Simulator):

	def __init__(self, **args):
		self.started = time.time()
		self.sim = None
		self.child = None
		self.return_code = None

		super().__init__(**args)

	@property
	def state(self):
		state = super().state

		state['uptime'] = time.time() - self.started
		state['version'] = '0.1.0'
		state['host'] = socket.getfqdn()
		state['kernel'] = os.uname()
		state['return_code'] = self.return_code

		return state

	def change_state(self, state):
		self.logger.info('Simulation generic')
		self._state = state
		self.publish_state()

	def start(self, message):
		# Start an external command
		if self.child:
			poll_result = self.child.poll() 
			if self.child.poll() == None:
				# Child process is running
				return
				
		self.return_code = None
		self.child = subprocess.Popen(["/usr/bin/ping", "google.de", "-c", "100"])
		self.change_state('running')

	def stop(self, message):
		# Stop the external command (kill)
		if self.child:
			self.child.terminate()
			poll_result = self.child.poll()
			if (poll_result != None):
				self.return_code = poll_result
			self.change_state('stopped')

	def pause(self, message):
		# Suspend command
		if self.child:
			poll_result = self.child.poll() 
			# Only send if child process is running
			if self.child.poll() == None:
				self.child.send_signal(signal.SIGSTOP)
				return

	def resume(self, message):
		# Let process run
		if self.child:
			poll_result = self.child.poll() 
			# Only send if child process is running and paused
			if self.child.poll() == -signal.SIGSTOP:
				self.child.send_signal(signal.SIGCONT)
				return

	def ping(self, message):
		if (self.child):
			poll_result = self.child.poll()
			if (poll_result != None):
				self.return_code = poll_result
		self.publish_state()

