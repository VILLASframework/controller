import time
import socket
import os
import sys
import threading
import re

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
		for regex in self.properties['whitelist']:
			if re.match(regex, argv0) is not None:
				valid = True
				break

		if not valid:
			self.logger.error('Executable "%s" is not whitelisted!' % argv0)
			self.change_state('failed')
			return

		self.logger.info('Execute: %s' % argv)
		self.child = subprocess.Popen(argv, **args, stdout = sys.stdout, stderr = subprocess.STDOUT)

		self.change_state('running')

		while self.child.returncode is None:
			self.child.poll()

			# Suspend the thread for some time
			# TODO: do we really need this?
			time.sleep(0.1)

		if self.child.returncode >= 0:
			self.return_code = self.child.returncode
			self.logger.info('Child process terminated with code: %d' % self.return_code)
			self.change_state('finished')
		elif self.child.returncode == -signal.SIGTERM:
			self.logger.info('Child process has been terminated by a signal')
			self.change_state('stopped')
		else:
			sig = signal.Signals(-self.child.returncode)
			self.logger.error('Child process caught signal: %s', sig.name)
			self.change_state('failed')

		self.child = None

	def reset(self, message):
		# Stop the external command (kill)
		if self.child is None:
			return

		# This is a hard reset!
		self.child.send_signal(signal.SIGKILL)

	def stop(self, message):
		# Stop the external command (kill)
		if self.child is None:
			self.change_state('error')
			self.logger.error('No child process is running')
			return

		self.child.terminate()
		self.logger.info('Send termination signal to child process')

	def pause(self, message):
		# Suspend command
		if self.child is None:
			self.change_state('error')
			self.logger.error('No child process is running')
			return

		self.child.send_signal(signal.SIGSTOP)
		self.change_state('paused')
		self.logger.info('Child process has been paused')

	def resume(self, message):
		# Let process run
		if self.child is None:
			self.change_state('error')
			self.logger.error('No child process is running')
			return

		self.child.send_signal(signal.SIGCONT)
		self.change_state('resumed')
		self.logger.info('Child process has been resumed')

	def ping(self, message):
		if (self.child):
			poll_result = self.child.poll()
			if (poll_result != None):
				self.return_code = poll_result

		self.publish_state()
