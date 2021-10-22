import time
import logging
import socket
import queue
import os
import kombu.mixins

from villas.controller.api import Api
from villas.controller import __version__ as version
from villas.controller.config import Config
from villas.controller.components.managers.generic import GenericManager


LOGGER = logging.getLogger(__name__)


class ControllerMixin(kombu.mixins.ConsumerProducerMixin):

    def __init__(self, connection, args):
        self.args = args
        self.config: Config = args.config

        self.connection = connection
        self.exchange = kombu.Exchange(name='villas',
                                       type='headers',
                                       durable=True)

        self.publish_queue = queue.Queue()

        # Components are activated by first call to on_iteration()
        self.components = {}
        self.active_components = {}

        manager = self.add_managers()

        comps = [c for c in self.config.components if c.enabled]
        for comp in comps:
            LOGGER.info('Adding %s', comp)
            manager.add_component(comp)

    def get_consumers(self, _, channel):
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

            mgr.mixin = self

            self.components[mgr.uuid] = mgr
        else:
            mgr = mgrs[0]

        return mgr

    def publish(self, body, **kwargs):
        self.publish_queue.put((body, kwargs))

    def _drain_publish_queue(self):
        try:
            while msg := self.publish_queue.get(False):
                body = msg[0]
                kwargs = msg[1]

                if 'exchange' not in kwargs:
                    kwargs['exchange'] = self.exchange

                self.producer.publish(body, **kwargs)
        except queue.Empty:
            pass

    def on_iteration(self):
        # Drain publish queue
        self._drain_publish_queue()

        # Update components
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

    def start(self):
        self.started = time.time()

        if self.config.api.enabled:
            self.api = Api(self)
            self.api.start()

        self.should_terminate = False
        while not self.should_terminate:
            self.should_stop = False

            LOGGER.info('Starting mixing for %d components',
                        len(self.active_components))

            super().run()

    def shutdown(self):
        LOGGER.info('Shutdown controller')

        for u, c in self.components.items():
            c.on_shutdown()

        # Publish last status updates before shutdown
        self._drain_publish_queue()
        self.should_terminate = True

    @property
    def status(self):
        u = os.uname()

        return {
            'version': version,
            'uptime': time.time() - self.started,
            'host': socket.gethostname(),
            'kernel': {
                'sysname': u.sysname,
                'nodename': u.nodename,
                'release': u.release,
                'version': u.version,
                'machine': u.machine
            },
        }
