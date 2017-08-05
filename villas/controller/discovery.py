import logging

from kombu import Consumer, Producer, Queue, Exchange
from kombu.pools import producers


LOGGER = logging.getLogger(__name__)

class Discovery(Consumer):

	def __init__(self, channel, simulators):
		self._simulators = simulators
		self._connection = channel
	
		self._exchange = Exchange(
			name = 'discover',
			type = 'direct',
			durable = True
		)
		
		super(Discovery, self).__init__(
			channel = channel,
			queues = Queue(
				exchange = self._exchange,
				exclusive = True
			),
			no_ack = True
		)

	def receive(self, body, message):
		LOGGER.debug("Received disco request: %s", body)

		with Producer(self._connection, exchange = self._exchange) as pr:
			for sim in self._simulators:
				pr.publish(
					body = { 'name': sim.name },
					routing_key = message.properties['reply_to'],
					correlation_id = message.properties['correlation_id'],
					retry = True,
				)
				
				LOGGER.debug("Disco reply: %s %s", message.properties['reply_to'], { 'name': sim.name })