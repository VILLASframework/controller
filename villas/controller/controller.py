import logging
import kombu.mixins

LOGGER = logging.getLogger(__name__)


class ControllerMixin(kombu.mixins.ConsumerMixin):

    def __init__(self, connection, components):
        self.components = {comp.uuid: comp for comp in components if comp.enabled}
        self.connection = connection

        for uuid, comp in self.components.items():
            LOGGER.info('Adding %s', comp)
            comp.set_mixin(self)
            comp.on_ready()

        self.active_components = self.components.copy()

    def get_consumers(self, Consumer, channel):
        return map(lambda comp: comp.get_consumer(channel),
                   self.active_components.values())

    def on_iteration(self):
        added_components = self.components.keys() - self.active_components.keys()
        removed_components = self.active_components.keys() - self.components.keys()
        if added_components or removed_components:
            LOGGER.info('Components changed. Restarting mixin')

            # We need to re-enter the contextmanager of the mixin
            # in order to consume messages for the new components
            self.should_stop = True

            for uuid in added_components:
                comp = self.components[uuid]

                LOGGER.info('Adding %s', comp)
                comp.set_mixin(self)

            for uuid in removed_components:
                comp = self.active_components[uuid]

                LOGGER.info('Removing %s', comp)

            self.active_components = self.components.copy()

    def run(self):
        while True:
            self.should_stop = False

            LOGGER.info('Startig mixing for %d components',
                        len(self.active_components))

            super().run()
