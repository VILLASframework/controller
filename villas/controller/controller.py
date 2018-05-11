import logging
import kombu.mixins

LOGGER = logging.getLogger(__name__)

class Controller(kombu.mixins.ConsumerMixin):

	def __init__(self, connection, simulators):
		self.simulators = simulators
		self.connection = connection

		for sim in simulators:
			LOGGER.info("Adding simulator: %s" % sim.uuid)
			sim.set_connection(connection)

	def get_consumers(self, Consumer, channel):
		return map(lambda sim: sim.get_consumer(channel), self.simulators)
