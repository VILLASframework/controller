import socket
import rtds
import threading
import time

from ..simulator import Simulator

class RTDSSimulator(Simulator):

	def __init__(self, **args):
		super().__init__(self, **args)

		self.host = args['host']
		self.number = args['number']
		self.interval = args['interval'] if 'interval' in args else 1

		self.rack = rtds.Rack(self.host, self.number)

		t = threading.Thread()
		t.start()

	def run(self):
		while True:
			user, case = self.rack.ping()

			time.sleep(self.interval)

	def __str__(self):
		return "%sSimulator #%d <%s: %s, host=%s>" % (self.type, self.number, self.name, self.uuid, self.host)

	@property
	def state(self):
		state = super().state

		state['user'] = self.current_user
		state['case'] = self.current_case

		return state
