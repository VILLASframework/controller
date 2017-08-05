import logging

from kombu import Consumer, Queue, Exchange

LOGGER = logging.getLogger(__name__)

class StatusConsumer(Consumer):

	def __init__(self, channel):
		super(StatusConsumer, self).__init__(
			channel,
			queues = Queue(
				exchange = Exchange(
					name = 'status',
					type = 'topic',
					durable = False
				),
				routing_key = 'status.simulator.#',
				exclusive = True
			),
			no_ack = True
		)

	def receive(self, body, message):
		LOGGER.info("Received %r" % body)