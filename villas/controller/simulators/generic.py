import sys
import threading
import re

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
			self.change_state('error')
			self.logger.error('Child process is already running');
			return

		try:
			params = message.payload['parameters']

			thread = threading.Thread(target = GenericSimulator.run, args = (self, params))
			thread.start()
		except:
			self.change_state('error')


	def run(self, params):
		# TODO: validate parameters against simulator properties (self.properties)
		args = { }

		argv0 = params['executable']
		argv = [argv0]

		if 'argv' in params:
			argv += [ str(x) for x in params['argv'] ]

		if 'shell' in params:
			if 'shell' not in self.properties or self.properties['shell'] != True:
				self.logger.error('Shell exeuction is not allowed!')
				self.change_state('failed')
				return

			args['shell'] = params['shell']
		if 'working_directory' in params:
			args['cwd'] = params['working_directory']
		if 'environment' in params:
			args['env'] = params['shell']

		valid = False
		self.logger.info(self.properties)
		if 'whitelist' in self.properties:
			for regex in self.properties['whitelist']:
				self.logger.info("Checking for match: " + regex)
				if re.match(regex, argv0) is not None:
					valid = True
					break

		if not valid:
			self.logger.error('Executable "%s" is not whitelisted!' % argv0)
			self.change_state('error')
			return

		if self.change_state('starting'):
			self.logger.info('Execute: %s' % argv)
			self.child = subprocess.Popen(argv, **args, stdout = sys.stdout, stderr = subprocess.STDOUT)

		if self.change_state('running'):
			self.child.wait()
			if self.child.returncode == 0:
				self.logger.info('Child process has finished.')
				self.change_state('stopping')
				self.change_state('idle')
			elif self.child.returncode > 0:
				self.return_code = self.child.returncode
				self.logger.info('Child process exited with code: %d' % self.return_code)
				self.change_state('error')
			elif self.child.returncode == -signal.SIGTERM:
				self.logger.info('Child process was terminated')
				self.change_state('idle')
			else:
				sig = signal.Signals(-self.child.returncode)
				self.logger.error('Child process caught signal: %s', sig.name)
				self.change_state('error')

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
			self.change_state('error')
			self.logger.error('No child process is running')
			return

		if self._state == 'paused':
			send_cont = True

		# Stop the external command (SIGTERM)
		if self.change_state('stopping'):
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
			self.change_state('error')
			self.logger.error('No child process is running')
			return

		if self.change_state('pausing'):
			self.child.send_signal(signal.SIGSTOP)
		if self.change_state('paused'):
			self.logger.info('Child process has been paused')

	def resume(self, message):
		# Let process run
		if self.child is None:
			self.change_state('error')
			self.logger.error('No child process is running')
			return

		if self.change_state('resuming'):
			self.child.send_signal(signal.SIGCONT)
		if self.change_state('running'):
			self.logger.info('Child process has resumed')

	def ping(self, message):
		if (self.child):
			poll_result = self.child.poll()
			if (poll_result != None):
				self.return_code = poll_result

		self.publish_state()
