import logging
import kombu
import time
import socket
import os
import uuid
import threading

from villas.controller import __version__ as version
from villas.controller.exceptions import SimulationException


class Component(object):

    def __init__(self, **props):
        self.realm = props.get('realm')
        self.type = props.get('type')
        self.name = props.get('name')
        self.category = props.get('category')
        self.enabled = props.get('enabled', True)
        self.uuid = props.get('uuid', str(uuid.uuid4()))

        self.started = time.time()
        self.properties = props

        self._state = 'idle'
        self._stateargs = {}

        self.logger = logging.getLogger(
            f'villas.controller.{self.category}.{self.type}:{self.uuid}')

        self.producer = None
        self.exchange = kombu.Exchange(name='villas',
                                       type='headers',
                                       durable=True)

        self.publish_state_interval = 10
        self.publish_state_thread_stop = threading.Evdasent()
        self.publish_state_thread = threading.Thread(
            target=self.publish_state_periodically)
        self.publish_state_thread.start()

    def __del__(self):
        self.publish_state_thread_stop.set()
        self.change_state('gone')

    def on_ready(self):
        pass

    def set_mixin(self, mixin):
        self.mixin = mixin
        self.connection = mixin.connection

        self.producer = kombu.Producer(channel=self.connection.channel(),
                                       exchange=self.exchange)

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
            'status': {
                'state': self._state,
                'version': version,
                'uptime': time.time() - self.started,
                'host': socket.gethostname(),
                'kernel': os.uname(),
            },
            'properties': self.properties,
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

        self.logger.info(f'State transition: {self._state} => {state} {kwargs}')  # noqa E501

        self._state = state
        self._stateargs = kwargs

        self.publish_state()

    # Actions
    def ping(self, message):
        self.publish_state()

    def start(self, message):
        raise SimulationException('The component can not be started')

    def stop(self, message):
        raise SimulationException('The component can not be stopped')

    def pause(self, message):
        raise SimulationException('The component can not be paused')

    def resume(self, message):
        raise SimulationException('The component can not be resumed')

    def shutdown(self, message):
        raise SimulationException('The component can not be shut down')

    def reset(self, message):
        self.started = time.time()

    @staticmethod
    def from_dict(dict):
        category = dict.get('category')

        if category == 'simulator':
            from villas.controller.components.simulator import Simulator
            return Simulator.from_dict(dict)
        elif category == 'controller':
            from villas.controller.components.controller import Controller
            return Controller.from_dict(dict)
        elif category == 'gateway':
            from villas.controller.components.gateway import Gateway
            return Gateway.from_dict(dict)
        else:
            raise Exception(f'Unsupported category {category}')

    def publish_state(self):
        if self.producer is None:
            return

        self.producer.publish(self.state, headers=self.headers)

    def publish_state_periodically(self):
        while not self.publish_state_thread_stop.wait(
          self.publish_state_interval):
            self.publish_state()

    def __str__(self):
        return f'{self.type} {self.category} <{self.name}: {self.uuid}>'
