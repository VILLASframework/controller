import logging
import kombu
import time
import socket
import os
import uuid

from villas.controller import __version__ as version
from villas.controller.exceptions import SimulationException


class Component(object):

    def __init__(self, **props):
        # Default values
        if 'enabled' not in props:
            props['enabled'] = True

        if 'uuid' not in props:
            props['uuid'] = str(uuid.uuid4())

        self.realm = props['realm']
        self.type = props['type']
        self.name = props['name']
        self.category = props['category']
        self.enabled = props['enabled']
        self.uuid = props['uuid']

        self.started = time.time()
        self.properties = props

        self._state = 'idle'
        self._stateargs = {}

        self.logger = logging.getLogger(
            f'villas.controller.{self.category}.{self.type}:{self.name}')

        self.producer = None
        self.exchange = kombu.Exchange(name='villas',
                                       type='headers',
                                       durable=True)

    def __del__(self):
        self.change_state('gone')

    def on_ready(self):
        pass

    def set_mixin(self, mixin):
        self.mixin = mixin
        self.connection = mixin.connection

        self.producer = kombu.Producer(channel=self.connection.channel(),
                                       exchange=self.exchange)

        self.publish_state()

    def get_consumer(self, channel):
        self.channel = channel

        return kombu.Consumer(
            channel=self.channel,
            on_message=self.on_message,
            queues=kombu.Queue(
                exchange=self.exchange,
                binding_arguments=self.headers,
                durable=False
            ),
            no_ack=True,
            accept={'application/json'}
        )

    @property
    def headers(self):
        return {
            'x-match': 'any',
            'category': self.category,
            'realm': self.realm,
            'uuid': self.uuid,
            'type': self.type,
            'action': 'ping'
        }

    @property
    def state(self):
        return {
            'state': self._state,
            'version': version,
            'properties': self.properties,
            'uptime': time.time() - self.started,
            'host': socket.gethostname(),
            'kernel': os.uname(),

            **self._stateargs
        }

    def on_message(self, message):
        self.logger.debug('Received message: %s', message.payload)

        if 'action' in message.payload:
            self.run_action(message.payload['action'], message)

    def run_action(self, action, message):
        if action == 'ping':
            self.logger.debug('Received action: %s', action)
        else:
            self.logger.info('Received action: %s', action)

        try:
            if action == 'ping':
                self.ping(message)
            elif action == 'start':
                self.change_state('starting')
                self.start(message)
            elif action == 'stop':
                # state changed to stopping after the simulation
                # has ended, to avoid missing log entries
                self.stop(message)
            elif action == 'pause':
                self.change_state('pausing')
                self.pause(message)
            elif action == 'resume':
                self.change_state('resuming')
                self.resume(message)
            elif action == 'shutdown':
                self.change_state('shuttingdown')
                self.shutdown(message)
            elif action == 'reset':
                self.change_state('resetting')
                self.reset(message)
            else:
                raise SimulationException(self, 'Unknown action',
                                          action=action)

        except SimulationException as se:
            self.change_state('error', msg=se.msg, **se.info)
        finally:
            message.ack()

    def change_state(self, state, **kwargs):
        if self._state == state:
            return

        self.logger.info(f'State transition: {self._state} => {state} {kwargs}')

        self._state = state
        self._stateargs = kwargs

        self.publish_state()

    # Actions
    def ping(self, message):
        self.publish_state()

    def start(self, message):
        pass

    def stop(self, message):
        pass

    def pause(self, message):
        pass

    def resume(self, message):
        pass

    def shutdown(self, message):
        pass

    def reset(self, message):
        self.started = time.time()

    @staticmethod
    def from_json(json):
        from villas.controller.components.controller import Controller
        from villas.controller.components.simulator import Simulator
        from villas.controller.components.gateway import Gateway

        if json['category'] == 'simulator':
            return Simulator.from_json(json)
        elif json['category'] == 'gateway':
            return Gateway.from_json(json)
        elif json['category'] == 'controller':
            return Controller.from_json(json)

    def publish_state(self):
        if self.producer is None:
            return

        self.producer.publish(self.state, headers=self.headers)

    def __str__(self):
        return f'{self.type} {self.category} <{self.name}: {self.uuid}>'
