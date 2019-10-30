import threading
import requests
import time

from villas.node.node import Node
from ..gateway import Gateway

class VILLASnodeNode(Gateway):

	def __init__(self, gateway, args):
		# Some default properties
		props = {
			'category' : 'villas'
		}

		if args['type'] == 'websocket':
			props['endpoint'] = gateway.node.api_endpoint + '/' + args['name']

		props.update(args)

		super().__init__(**props)

		self.name = args['name']
		self._state = args['state']

		self.gateway = gateway

	def start(self, message):
		try:
			self.gateway.node.request('node.start', { 'node' : self.name })
			self.gateway.check_state()
		except:
			self.logger.warn('Failed to start node')

	def stop(self, message):
		try:
			self.gateway.node.request('node.stop', { 'node' : self.name })
			self.gateway.check_state()
		except:
			self.logger.warn('Failed to stop node')

	def pause(self, message):
		try:
			self.gateway.node.request('node.pause', { 'node' : self.name })
			self.gateway.check_state()
		except:
			self.logger.warn('Failed to pause node')

	def resume(self, message):
		try:
			self.gateway.node.request('node.resume', { 'node' : self.name })
			self.gateway.check_state()
		except:
			self.logger.warn('Failed to resume node')

	def reset(self, message):
		try:
			self.gateway.node.reset('node.restart', { 'node' : self.name })
			self.gateway.check_state()
		except:
			self.logger.warn('Failed to reset node')

class VILLASnodeGateway(Gateway):

	def __init__(self, **args):
		super().__init__(**args)

		self.node = Node(**args)
		self.nodes = []

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
		if not self.enabled:
			return

		try:
			for node in self.node.nodes:
				found = False
				for comp in self.controller.components:
					if comp.uuid == node['uuid']:
						found = True
						break

				if found:
					comp.change_state(node['state'])
				else:
					node = VILLASnodeNode(self, node)

					self.nodes.append(node)
					self.controller.components.add(node)

			self.change_state('running')

		except requests.RequestException as e:
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

		if self.autostart and not self.node.is_running():
			self.start()

	def start(self, message = None):
		self.node.start()

		self.change_state('starting')

	def stop(self, message):
		if self.node.is_running():
			self.node.stop()

		self.change_state('idle')

		# Once the gateway shutsdown, all the gateway nodes are also shutdown
		for node in self.nodes:
			node.change_state('shutdown')

	def pause(self, message):
		self.node.pause()

		self.change_state('paused')

		# Once the gateway shutsdown, all the gateway nodes are also shutdown
		for node in self.nodes:
			node.change_state('paused')

	def resume(self, message):
		self.node.resume()

	def reset(self, message):
		self.node.restart()
