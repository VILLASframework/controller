import logging
import kombu
import uuid

class Simulator(object):

	def __init__(self, **args):
		self.realm = args['realm']
		self.type = args['type']
		self.uuid = args['uuid'] or uuid.uuid4()

		self.properties = args

		self.model = None
		self._state = 'unknown'

		self.logger = logging.getLogger("villas.controller.simulator:" + self.uuid)

		self.exchange = kombu.Exchange(
			name = 'villas',
			type = 'headers',
			durable = True
		)

	def set_connection(self, connection):
		self.connection = connection

		self.producer = kombu.Producer(
			channel = self.connection.channel(),
			exchange = self.exchange
		)

	@staticmethod
	def from_json(json):
		from .simulators import dummy, generic, rtlab, rscad

		if json['type'] == "dummy":
			return dummy.DummySimulator(**json)
		if json['type'] == "generic":
			return generic.GenericSimulator(**json)
		elif json['type'] == "dpsim":
			from .simulators import dpsim
			return dpsim.DPsimSimulator(**json)
		elif json['type'] == "rtlab":
			return dpsim.RTLabSimulator(**json)
		elif json['type'] == "rscad":
			return dpsim.RSCADSimulator(**json)
		else:
			return None

	def get_consumer(self, channel):
		self.channel = channel

		return kombu.Consumer(
			channel = self.channel,
			on_message = self.on_message,
			queues = kombu.Queue(
				exchange = self.exchange,
				binding_arguments = self.headers,
				durable = False
			),
			no_ack = True
		)

	@property
	def headers(self):
		return {
			'x-match' : 'any',
			'category' : 'simulator',
			'realm' : self.realm,
			'uuid' : self.uuid
		}

	def on_message(self, message):
		self.logger.debug("Received message: %s: %s", message, message.payload)

		if 'action' not in message.payload:
			return

		action = message.payload['action']

		if action == 'ping':
			self.ping(message)
		elif action == 'start':
			self.start(message)
		elif action == 'stop':
			self.stop(message)
		elif action == 'pause':
			self.pause(message)
		elif action == 'resume':
			self.resume(message)
		elif action == 'shutdown':
			self.shutdown(message)
		elif action == 'reset':
			self.reset(message)

		message.ack()

	@property
	def state(self):
		state = {
			'state' : self._state,
			'model' : self.model,
			'properties' : self.properties
		}

		return state

	def publish_state(self):
		self.producer.publish(
			self.state,
			headers = self.headers
		)

	# Actions
	def ping(self, message):
		self.publish_state()

	def start(self, message):
		pass

	def stop(self, message):
		pass

	def pause(self, message):
		pass

	def resume(self, message):
		pass

	def __str__(self):
		return "Simulator <%s, %s>" % (self.type, self.uuid)
