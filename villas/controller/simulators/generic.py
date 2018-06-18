import sys
import threading
import re

from ..exceptions import SimulationException
from .. import simulator
import subprocess, signal

class GenericSimulator(simulator.Simulator):

	def __init__(self, **args):
		self.child = None
		self.return_code = None

		super().__init__(**args)

	@property
	def state(self):
		state = super().state

		state['return_code'] = self.return_code

		return state

	def start(self, message):
		# Start an external command
		if self.child is not None:
			raise SimulationException(self, 'Child process is already running')

		try:
			params = message.payload['parameters']

			thread = threading.Thread(target = GenericSimulator.run, args = (self, params))
			thread.start()
		except Exception as e:
			self.change_state('error', msg = 'Failed to start child process: %s' % e)

	def run(self, params):
		try:
			args = { }
			argv0 = params['executable']
			argv = [argv0]

			if 'argv' in params:
				argv += [ str(x) for x in params['argv'] ]

			if 'shell' in params:
				if 'shell' not in self.properties or self.properties['shell'] != True:
					raise SimulationException(self, 'Shell exeuction is not allowed!')

				args['shell'] = params['shell']

			if 'working_directory' in params:
				args['cwd'] = params['working_directory']

			if 'environment' in params:
				args['env'] = params['shell']

			valid = False
			if 'whitelist' in self.properties:
				for regex in self.properties['whitelist']:
					self.logger.info("Checking for match: " + regex)
					if re.match(regex, argv0) is not None:
						valid = True
						break

			if not valid:
				raise SimulationException(self, 'Executable is not whitelisted for this simulator', executable = argv0)

			self.logger.info('Execute: %s' % argv)
			self.child = subprocess.Popen(argv, **args, stdout = sys.stdout, stderr = subprocess.STDOUT)

			self.change_state('running')

			self.child.wait()
			if self.child.returncode == 0:
				self.logger.info('Child process has finished.')
				self.change_state('stopping')
				self.change_state('idle')
			elif self.child.returncode > 0:
				self.return_code = self.child.returncode
				raise SimulationException(self, 'Child process exited', code = self.return_code)
			elif self.child.returncode == -signal.SIGTERM:
				self.logger.info('Child process was terminated successfully')
				self.change_state('idle')
			else:
				sig = signal.Signals(-self.child.returncode)
				raise SimulationException(self, 'Child process caught signal', signal = -self.child.returncode, signal_name = sig.name)
		except SimulationException as se:
			self.change_state('error', msg = se.msg, **se.info)

		self.child = None

	def reset(self, message):
		self.change_state('idle')

		# Don't send a signal if the child does not exist
		if self.child is None:
			return

		# Stop the external command (kill)
		# This is a hard reset!
		self.child.send_signal(signal.SIGKILL)

	def stop(self, message):
		send_cont = False

		if self.child is None:
			raise SimulationException(self, 'No child process is running')

		if self._state == 'paused':
			send_cont = True

		# Stop the external command (SIGTERM)
		self.child.terminate()
		self.logger.info('Send termination signal to child process')

		# If the process has been paused, we must resume it
		# so that it can process the SIGTERM and exit
		if send_cont:
			self.child.send_signal(signal.SIGCONT)

		# final transition to idle state occurs in run thread

	def pause(self, message):
		# Suspend command
		if self.child is None:
			raise SimulationException(self, 'No child process is running')

		self.child.send_signal(signal.SIGSTOP)

		self.change_state('paused')
		self.logger.info('Child process has been paused')

	def resume(self, message):
		# Let process run
		if self.child is None:
			raise SimulationException(self, 'No child process is running')

		self.child.send_signal(signal.SIGCONT)

		self.change_state('running')
		self.logger.info('Child process has resumed')
