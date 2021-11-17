import logging
import os.path
import time
import kombu
import uuid
import threading
import yaml
import jsonschema
from jsonschema import Draft202012Validator

import importlib
import importlib.resources as resources

from villas.controller.exceptions import SimulationException


class Component:

    def __init__(self, **props):
        self.realm = props.get('realm')
        self.type = props.get('type')
        self.name = props.get('name')
        self.category = props.get('category')
        self.enabled = props.get('enabled', True)
        self.location = props.get('location', '')
        self.uuid = props.get('uuid')

        # The manager component which manages this instances
        self.manager = None

        # Generate random UUID in case no one is provided
        if not self.uuid:
            self.uuid = str(uuid.uuid4())

        self.started = time.time()
        self.properties = props

        self._state = 'idle'
        self._status_fields = {}

        self.logger = logging.getLogger(
            f'villas.controller.{self.category}.{self.type}:{self.uuid}')

        self._schema = self.load_schema()

        self.publish_status_interval = 30
        self.publish_status_thread_stop = threading.Event()
        self.publish_status_thread = threading.Thread(
            target=self.publish_status_periodically)

    def on_ready(self):
        self.publish_status_thread.start()
        pass

    def on_shutdown(self):
        if self.publish_status_thread.is_alive():
            self.publish_status_thread_stop.set()
            self.publish_status_thread.join()

    def set_manager(self, manager):
        self.manager = manager

    def set_mixin(self, mixin):
        self.mixin = mixin
        self.connection = mixin.connection

        self.workdir = os.path.join(self.mixin.config.workdir, str(self.uuid))

    def get_consumer(self, channel):
        self.channel = channel

        return kombu.Consumer(
            channel=self.channel,
            on_message=self.on_message,
            queues=kombu.Queue(
                exchange=self.mixin.exchange,
                binding_arguments={
                    'x-match': 'any',
                    **self.headers
                },
                durable=False,
                exclusive=True,
                auto_delete=True
            ),
            no_ack=True,
            accept={'application/json'}
        )

    @property
    def schema(self):
        return self._schema

    def load_schema(self):
        schema = {}

        try:
            pkg_name = f'villas.controller.schemas.{self.category}.{self.type}'
            pkg = importlib.import_module(pkg_name)
        except ModuleNotFoundError:
            self.logger.warn('Missing schemas!')

            return schema

        for res in resources.contents(pkg):
            name, ext = os.path.splitext(res)
            if resources.is_resource(pkg, res) and ext in ['.yaml', '.json']:

                fo = resources.open_text(pkg, res)
                loadedschema = yaml.load(fo, yaml.SafeLoader)

                schema[name] = Draft202012Validator(loadedschema)

        return schema

    def validate_parameters(self, action, parameters):
        if action in self.schema:
            validator = self.schema[action]

            validator.validate(parameters)

        else:
            self.logger.warn('missing schema for action: %s', action)
            return True  # we really should fail here...

    @property
    def headers(self):
        return {
            'category': self.category,
            'realm': self.realm,
            'uuid': self.uuid,
            'type': self.type
        }

    @property
    def status(self):
        status = {
            'state': self._state,
            **self.mixin.status,
            **self._status_fields
        }

        if self.manager is not None:
            status['managed_by'] = self.manager.uuid

        return {
            'status': status,
            'properties': {
                **self.properties,
                **self.headers
            },
            'schema': {
                name: v.schema for name, v in self.schema.items()
            }
        }

    def on_message(self, message):
        self.logger.info('my uuid: %s', self.uuid)
        self.logger.info('Received message: %s', message.payload)

        if 'action' in message.payload:
            try:
                self.run_action(message.payload['action'], message.payload)
            except SimulationException:
                pass

        message.ack()

    def run_action(self, action, payload):
        if action == 'ping':
            self.logger.debug('Received action: %s', action)
        else:
            self.logger.info('Received action: %s', action)

        parameters = payload.get('parameters', {})

        try:
            self.validate_parameters(action, parameters)
        except jsonschema.ValidationError as ve:
            e = {
                'instance': ve.instance,
                'path': ve.json_path,
            }

            se = SimulationException(self, 'Failed to validate parameters',
                                     **e)

            self.logger.error('Failed to validate action parameters against '
                              'schema: %s', ve.message)
            self.change_to_error(ve.message, **e)

            raise se

        try:
            if action == 'ping':
                self.ping(payload)
            elif action == 'start':
                self.change_state('starting')
                self.start(payload)
            elif action == 'stop':
                self.change_state('stopping')
                self.stop(payload)
            elif action == 'pause':
                self.change_state('pausing')
                self.pause(payload)
            elif action == 'resume':
                self.change_state('resuming')
                self.resume(payload)
            elif action == 'shutdown':
                self.change_state('shuttingdown')
                self.shutdown(payload)
            elif action == 'reset':
                self.change_state('resetting')
                self.reset(payload)
            else:
                raise SimulationException(self, 'Unknown action',
                                          action=action)

        except SimulationException as se:
            self.logger.error('SimulationException: %s', str(se))
            self.change_to_error(se.msg, **se.info)

            raise se

    def change_state(self, state, **kwargs):
        if self._state == state:
            return

        self.logger.info(f'State transition: {self._state} => {state} {kwargs}')  # noqa E501

        self._state = state
        self._status_fields = kwargs

        self.publish_status()

    def change_to_error(self, msg, **details):
        self.change_state('error',
                          error={
                              'msg': msg,
                              **details
                          })

    # Actions
    def ping(self, payload):
        self.publish_status()

    def start(self, payload):
        raise SimulationException('The component can not be started')

    def stop(self, payload):
        raise SimulationException('The component can not be stopped')

    def pause(self, payload):
        raise SimulationException('The component can not be paused')

    def resume(self, payload):
        raise SimulationException('The component can not be resumed')

    def shutdown(self, payload):
        raise SimulationException('The component can not be shut down')

    def reset(self, payload):
        self.started = time.time()

    @staticmethod
    def from_dict(dict):
        category = dict.get('category')

        if category == 'simulator':
            from villas.controller.components.simulator import Simulator
            return Simulator.from_dict(dict)
        elif category == 'manager':
            from villas.controller.components.manager import Manager
            return Manager.from_dict(dict)
        elif category == 'gateway':
            from villas.controller.components.gateway import Gateway
            return Gateway.from_dict(dict)
        else:
            raise Exception(f'Unsupported category {category}')

    def publish_status(self):
        if not self.mixin:
            return

        self.mixin.publish(self.status, headers=self.headers)

    def publish_status_periodically(self):
        self.logger.info('Start state publish thread')

        while not self.publish_status_thread_stop.wait(
          self.publish_status_interval):
            self.logger.info('Publish status: %s', self.status)
            self.publish_status()

        self.logger.info('Stopping publish thread of %s', self.name)

    def __str__(self):
        return f'{self.type} {self.category} <{self.name}: {self.uuid}>'
