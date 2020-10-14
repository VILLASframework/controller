import logging
import kombu.mixins

LOGGER = logging.getLogger(__name__)


class Controller(kombu.mixins.ConsumerMixin):

    def __init__(self, connection, components):
        self.components = {comp for comp in components if comp.enabled}
        self.connection = connection

        for comp in self.components:
            LOGGER.info('Adding %s', str(comp))
            comp.set_controller(self)
            comp.on_ready()

        self.active_components = self.components.copy()

    def get_consumers(self, Consumer, channel):
        return map(lambda comp: comp.get_consumer(channel),
                   self.active_components)

    def on_iteration(self):
        added_components = self.components - self.active_components
        removed_components = self.active_components - self.components
        if added_components or removed_components:
            LOGGER.info('Components changed. Restarting mixin')

            # We need to re-enter the contextmanager of the mixin
            # in order to consume messages for the new components
            self.should_stop = True

            for comp in added_components:
                LOGGER.info('Adding %s', comp)
                comp.set_controller(self)

            for comp in removed_components:
                LOGGER.info('Removing %s', comp)

            self.active_components = self.components.copy()

    def run(self):
        while True:
            self.should_stop = False

            LOGGER.info('Startig mixing for %d components',
                        len(self.active_components))

            super().run()
