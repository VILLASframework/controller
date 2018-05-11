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
			self.logger.info('Starting simulation...')

			t = threading.Timer(1.0, DummySimulator.change_state, args=[self, 'running'])
			t.start()

			change_state('starting')
		else:
			self.logger.warn('Attempted to start non-stopped simulator')

	def stop(self, message):
		if self._state == 'running':
			self.logger.info('Stopping simulation...')

			t = threading.Timer(1.0, DummySimulator.change_state, args=[self, 'stopped'])
			t.start()

			change_state('stopping')
		else:
			self.logger.warn('Attempted to stop non-running simulator')

	def pause(self, message):
		if self._state == 'running':
			self.logger.info('Pausing simulation...')

			t = threading.Timer(1.0, DummySimulator.change_state, args=[self, 'paused'])
			t.start()

			change_state('pausing')
		else:
			self.logger.warn('Attempted to pause non-running simulator')

	def resume(self, message):
		if self._state == 'paused':
			self.logger.info('Resuming simulation...')

			t = threading.Timer(1.0, DummySimulator.change_state, args=[self, 'running'])
			t.start()

			change_state('resuming')
		else:
			self.logger.warn('Attempted to resume non-paused simulator')

	def shutdown(self, message):
		self.logger.info('Shutdown simulator...')

		t = threading.Timer(1.0, DummySimulator.change_state, args=[self, 'shutdown'])
		t.start()

		change_state('shuttingdown')

	def reset(self, message):
		self.logger.info('Resetting simulator...')

		t = threading.Timer(1.0, DummySimulator.change_state, args=[self, 'idle'])
		t.start()

		self.started = time.time()

		change_state('resetting')
