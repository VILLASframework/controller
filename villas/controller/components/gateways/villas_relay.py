import threading
import requests
import time

from ..gateway import Gateway

class VILLASnodeRelaySession(Gateway):

	def __init__(self, gateway, args):
		# Some default properties
		props = {
			'category' : 'villas'
		}

		if args['type'] == 'websocket':
			props['endpoint'] = gateway.endpoint + '/' + args['identifier']

		props.update(args)

		super().__init__(**props)

		self.name = args['identifier']
		self._state = args['state']

		self.gateway = gateway

class VILLASnodeRelay(Gateway):

	def __init__(self, **args):
		super().__init__(**args)

		self.sessions = []
		self.endpoint = 'http://localhost:8088'
		self.api_endpoint = self.endpoint + '/api/v1'

		if 'autostart' in args:
			self.autostart = args['autostart']
		else:
			self.autostart = False

		self.version = 'unknown'

		self.thread_stop = threading.Event()
		self.thread = threading.Thread(target = self.check_state_periodically)
		self.thread.start()

	def __del__(self):
		self.thread_stop.set()
		self.thread.join()

	def check_state_periodically(self):
		while not self.thread_stop.wait(2):
			self.check_state()

	def check_state(self):
		try:
			r = requests.get(self.api_endpoint)
			r.raise_for_status()

			for session in r.json['sessions']:
				found = False
				for comp in self.controller.components:
					if comp.uuid == session['uuid']:
						found = True
						break

				if found:
					comp.change_state('running')
				else:
					session = VILLASnodeRelaySession(self, session)

					self.sessions.append(session)
					self.controller.components.add(session)

			self.change_state('running')

		except requests.RequestException:
			self.change_state('idle')

	@property
	def state(self):
		return {
			'villas_version' : self.version,

			**super().state
		}

	def on_ready(self):
		try:
			self.version = self.node.get_version()

		except:
			self.change_state('error', error='VILLASnode not installed')

		if self.autostart:
			self.start()

	def start(self, message = None):


		self.change_state('starting')

	def stop(self, message):


		self.change_state('idle')

		# Once the gateway shutsdown, all the gateway nodes are also shutdown
		for session in self.sessions:
			session.change_state('shutdown')

	def pause(self, message):


		# Once the gateway is paused, all the gateway nodes are also paused
		for session in self.sessions:
			session.change_state('paused')

	def resume(self, message):
		pass

	def reset(self, message):
		pass
