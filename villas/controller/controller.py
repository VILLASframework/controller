import logging
import socket
import kombu.mixins

from villas.controller.components.managers.generic import GenericManager

LOGGER = logging.getLogger(__name__)


class ControllerMixin(kombu.mixins.ConsumerMixin):

    def __init__(self, connection, components):
        self.components = {c.uuid: c for c in components if c.enabled}
        self.connection = connection

        manager = self.add_managers()

        for uuid, comp in self.components.items():
            LOGGER.info('Adding %s', comp)
            comp.set_manager(manager)

        # Components are activated by first call to on_iteration()
        self.active_components = {}

    def get_consumers(self, Consumer, channel):
        return map(lambda comp: comp.get_consumer(channel),
                   self.active_components.values())

    def add_managers(self):
        mgrs = [c for c in self.components.values()
                if isinstance(c, GenericManager)]

        # Check that not more than one generic manager is configured
        if len(mgrs) > 1:
            raise RuntimeError('Each VILLAScontoller instance can have '
                               'only a single generic manager configured!')

        # Add a generic manager if none is configured
        elif len(mgrs) == 0:
            mgr = GenericManager(
                type='generic',
                category='manager',
                name='Generic Manager',
                location=socket.gethostname()
            )

            self.components[mgr.uuid] = mgr
        else:
            mgr = mgrs[0]

        return mgr

    def on_iteration(self):
        added = self.components.keys() - self.active_components.keys()
        removed = self.active_components.keys() - self.components.keys()
        if added or removed:
            LOGGER.info('Components changed. Restarting mixin')

            # We need to re-enter the contextmanager of the mixin
            # in order to consume messages for the new components
            self.should_stop = True

            for uuid in added:
                comp = self.components[uuid]

                LOGGER.info('Adding %s', comp)
                comp.set_mixin(self)
                comp.on_ready()

            for uuid in removed:
                comp = self.active_components[uuid]

                LOGGER.info('Removing %s', comp)

            self.active_components = self.components.copy()

    def run(self):
        while True:
            self.should_stop = False

            LOGGER.info('Startig mixing for %d components',
                        len(self.active_components))

            super().run()

    def shutdown(self):
        LOGGER.info('Shutdown controller')
        for u, c in self.components.items():
            c.on_shutdown()

        self.connection.drain_events(timeout=3)
