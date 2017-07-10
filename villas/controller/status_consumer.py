import pika
import logging
import json

from villas.amqp.channel import Channel

LOGGER = logging.getLogger(__name__)

class Consumer(Channel):

	def __init__(self, connection):
		super(self.__class__, self).__init__(connection)
		
	def on_open(self, channel):
		super(self.__class__, self).on_open(channel)
		
		self.setup_exchange()
		
	def setup_exchange():
		LOGGER.info('Configure Exchange')

		self._exchange = self._channel.exchange_declare(
			callback = self.setup_queue,
			exchange = 'status',
			type = 'topic'
		)
	
	def setup_queue():
		LOGGER.info('Configure Queue')
		
		self._queue = self._channel.queue_declare(
			callback = self.bind_queue,
			queue = '',
			exclusive = True
		)
	
	def bind_queue():
		LOGGER.info('Bond Queue')

		self._channel.queue_bind(
			exchange = 'status',
			queue = self._queue.method.queue,
			routing_key = 'status.simulator.#'
		)

class StatusConsumer(Consumer):

	def __init__(self, connection):
		super(self.__class__, self).__init__(connection)

	def callback(self, channel, method, properties, body):
		json_body = json.loads(body)

		print("Received %r" % json_body)

	def consume_message(self):
		self._channel.basic_consume(
			self.callback,
			queue = queue.method.queue,
			no_ack = True
		)

		

	def send(self):
		state = self._simulator.get_state()
	
		self._channel.basic_publish(
			exchange = 'status',
			routing_key = 'status.simulator.rtds.rack1',
			body = json.dumps(state),
			properties = pika.BasicProperties(content_type='application/json')
		)
		
		self.schedule_message()