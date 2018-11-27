import logging
import kombu.mixins

LOGGER = logging.getLogger(__name__)

class Controller(kombu.mixins.ConsumerMixin):

	def __init__(self, connection, components):
		self.components = { comp for comp in components if comp.enabled }
		self.connection = connection

		for comp in self.components:
			LOGGER.info('Adding %s', str(comp))
			comp.set_controller(self)

		self.active_components = self.components.copy()

		for comp in self.components.copy():
			comp.on_ready()

	def get_consumers(self, Consumer, channel):
		return map(lambda comp: comp.get_consumer(channel), self.active_components)

	def on_iteration(self):
		new_components = self.components - self.active_components
		if new_components:
			LOGGER.info('Components changed. Restarting mixin')

			# We need to re-enter the contextmanager of the mixin
			# in order to consume messages for the new compoents
			self.should_stop = True

			for comp in new_components:
				LOGGER.info('Adding %s', str(comp))
				comp.set_controller(self)

			self.active_components = self.components.copy()

	def run(self):
		while True:
			self.should_stop = False

			LOGGER.info('Startig mixing for %d components' % len(self.active_components))

			super().run()
