import dpsim
import dpsim.components.dp as dp
import time
import socket
import os

from .. import simulator

class DPsimSimulator(simulator.Simulator):

	def __init__(self, **args):
		args['type'] = 'dpsim'

		self.started = time.time()
		self.sim = None

		super().__init__(**args)

	@property
	def headers(self):
		headers = super().headers

		headers['type'] = 'dpsim'
		headers['version'] = '0.1.0'

		return headers

	@property
	def state(self):
		state = super().state

		state['uptime'] = time.time() - self.started
		state['version'] = '0.1.0'
		state['host'] = socket.getfqdn()
		state['kernel'] = os.uname()

		return state

	def load_cim(self, fp):
		if fp != None:
			try:
				self.sim = dpsim.load_cim(fp.name)
				self.logger.info(simulation)
				os.unlink(fp.name)
			except IOError:
				self.logger.error('Failed to process url: ' + url + ' in temporary file: ' + fp.name)

	def start(self, message):
		fp = self.check_download(message)
		if (fp):
			self.load_cim(fp)

		if self.change_state('starting'):
			self.logger.info('Starting simulation...')

			self.logger.info(self.sim)
			if (self.sim.start() == None):
				self.change_state('running')
			else:
				self.change_state('error')
				self.logger.warn('Attempt to start simulator failed. State is ' + self._state)
		else:
			self.logger.warn('Attempted to start non-stopped simulator. State is ' + self._state)

	def stop(self, message):
		if self._state == 'running':
			self.logger.info('Stopping simulation...')

			if (self.sim and self.sim.stop() == None):
				self.change_state('stopped')
				self.logger.warn('State changed to ' + self._state)
			else:
				self.change_state('unknown')
				self.logger.warn('Attempt to stop simulator failed. State is ' + self._state)
		else:
			self.logger.warn('Attempted to stop non-stopped simulator. State is ' + self._state)

	def pause(self, message):
		if self._state == 'running':
			self.logger.info('Pausing simulation...')

			self._state = 'pausing'

			try:
				if (self.sim and self.sim.pause() == None):
					self.change_state('paused')
					self.logger.warn('State changed to ' + self._state)
				else:
					self.logger.warn('Attempted to pause simulator failed.')
					self.change_state('unknown')

			except SystemError as e:
				self.logger.warn('Attempted to pause simulator failed. Error is ' + str(e))
				self.change_state('unknown')

		else:
			self.logger.warn('Attempted to pause non-running simulator. State is ' + self._state)

	def resume(self, message):
		if self._state == 'paused':
			self.logger.info('Resuming simulation...')

			self._state = 'resuming'

			try:
				if (self.sim and self.sim.start() == None):
					self.change_state('running')
					self.logger.warn('State changed to ' + self._state)
				else:
					self.logger.warn('Attempted to resume simulator failed.')
					self.change_state('unknown')

			except SystemError as e:
				self.logger.warn('Attempted to pause simulator failed. Error is ' + str(e))
				self.change_state('unknown')

		else:
			self.logger.warn('Attempted to resume non-paused simulator. State is ' + self._state)
