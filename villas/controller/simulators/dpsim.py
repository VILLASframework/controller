import dpsim
import dpsim.components.dp as dp
import time
import socket
import os
import pycurl
import tempfile
from io import BytesIO

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

	def change_state(self, state):
		self.logger.info('Simulation dpsim')
		self._state = state
		self.publish_state()

	def loadCIMURL(self, url):
		try:
			buffer = BytesIO()
			c = pycurl.Curl()
			c.setopt(c.URL, url)
			c.setopt(c.WRITEDATA, buffer)
			c.perform()
			c.close()
		except pycurl.error:
			self.logger.error('Failed to load url: ' + url)

		try:
			fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
			fp.write(buffer.getvalue())
			fp.close()
			dpsim.load_cim(fp.name)
			os.unlink(fp.name)
		except IOError:
			self.logger.error('Failed to process url: ' + url + ' in temporary file: ' + fp.name)

	def start(self, message):
		if message.properties:
			if message.properties['application_headers']:
				if message.properties['application_headers']['uuid']:
					self.logger.info('Starting simulation for url: ' + str(message.properties['application_headers']['uuid']))
					self.loadCIMURL(str(message.properties['application_headers']['uuid']))

		if self._state not in ['stopped', 'unknown'] :
			self.logger.info('Starting simulation...')
			self.change_state('starting')

			self.sim = dpsim.Simulation('IdealVS_R1',
				[
					dp.VoltageSource("v_in", 1, 0, 10),
					dp.Resistor("r_1", 0, -1, 1),
					dp.Resistor("r_2", 1, -1, 1),
					dp.Resistor("r_3", 1, -1, 1)
				],
				duration=3000.0
			)

			if (self.sim.start() == None):
				self.change_state('running')
				self.logger.warn('State changed to ' + self._state)
			else:
				self.change_state('unknown')
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
