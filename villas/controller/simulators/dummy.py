import time
import threading
import os
import socket

import time

from .. import simulator

class DummySimulator(simulator.Simulator):

	def __init__(self, **args):
		args['type'] = 'dummy'

		self.started = time.time()

		super().__init__(**args)

	@property
	def headers(self):
		headers = super().headers

		headers['type'] = 'dummy'

		return headers

	@property
	def state(self):
		state = super().state

		state['uptime'] = time.time() - self.started
		state['version'] = '0.1.0'
		state['host'] = socket.getfqdn()
		state['kernel'] = os.uname()

		return state

	def change_state(self, state):
		self.logger.info('Simulation %s' % state)
		self._state = state
		self.publish_state()

	def start(self, message):
		if self._state not in ['stopped', 'unkown'] :
			t = threading.Timer(1.0, DummySimulator.change_state, args=[self, 'running'])
			t.start()

			self.change_state('starting')
		else:
			self.logger.warn('Attempted to start non-stopped simulator')
			self.change_state('error')

	def stop(self, message):
		if self._state == 'running':
			t = threading.Timer(1.0, DummySimulator.change_state, args=[self, 'stopped'])
			t.start()

			self.change_state('stopping')
		else:
			self.logger.warn('Attempted to stop non-running simulator')
			self.change_state('error')

	def pause(self, message):
		if self._state == 'running':
			t = threading.Timer(1.0, DummySimulator.change_state, args=[self, 'paused'])
			t.start()

			self.change_state('pausing')
		else:
			self.logger.warn('Attempted to pause non-running simulator')
			self.change_state('error')

	def resume(self, message):
		if self._state == 'paused':
			t = threading.Timer(1.0, DummySimulator.change_state, args=[self, 'running'])
			t.start()

			self.change_state('resuming')
		else:
			self.logger.warn('Attempted to resume non-paused simulator')
			self.change_state('error')

	def shutdown(self, message):
		t = threading.Timer(1.0, DummySimulator.change_state, args=[self, 'shutdown'])
		t.start()

		self.change_state('shuttingdown')

	def reset(self, message):
		t = threading.Timer(1.0, DummySimulator.change_state, args=[self, 'idle'])
		t.start()

		self.started = time.time()

		self.change_state('resetting')
