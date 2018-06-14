import logging
import kombu.mixins

LOGGER = logging.getLogger(__name__)

class Controller(kombu.mixins.ConsumerMixin):

	def __init__(self, connection, simulators):
		self.simulators = [ sim for sim in simulators if sim.enabled ]
		self.connection = connection

		for sim in self.simulators:
			LOGGER.info('Adding %s', str(sim))
			sim.set_connection(connection)

	def get_consumers(self, Consumer, channel):
		return map(lambda sim: sim.get_consumer(channel), self.simulators)
