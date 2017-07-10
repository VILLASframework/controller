import pika
import logging
import json

from villas.amqp.channel import Channel

LOGGER = logging.getLogger(__name__)

class StatusPublisher(Channel):

	def __init__(self, connection, simulator):
		super(self.__class__, self).__init__(connection)
		
		self._simulator = simulator
		
	def on_open(self, channel):
		super(self.__class__, self).on_open(channel)
		
		self.schedule_message()
	
	def schedule_message(self):
		self._timeout = self._connection.add_timeout(1.0, self.send)

	def configure(self):
		self._exchange = self._channel.exchange_declare(
			exchange = 'status',
			type = 'topic'
		)
		
		LOGGER.info('Configure from StatusPubsliher')

	def send(self):
		state = self._simulator.get_state()
	
		self._channel.basic_publish(
			exchange = 'status',
			routing_key = 'status.simulator.rtds.rack1',
			body = json.dumps(state),
			properties = pika.BasicProperties(content_type='application/json')
		)
		
		self.schedule_message()

	def on_closed(self, channel, reply_code, reply_text):
		self._connection.remove_timeout(self._timeout)
		
		super(self.__class__, self).on_closed(channel, reply_code, reply_text)