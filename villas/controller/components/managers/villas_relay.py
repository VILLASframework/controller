import threading
import requests
import os

from villas.controller.components.manager import Manager
from villas.controller.components.gateways.villas_relay import VILLASrelayGateway  # noqa E501


class VILLASrelayManager(Manager):

    def __init__(self, **args):
        self.autostart = args.get('autostart', False)
        self.api_url = args.get('api_url', 'http://localhost:8088') + '/api/v1'
        self.api_url_external = args.get('api_url_external', self.api_url)
        self._version = '-1'

        uuid = self.get_uuid()
        if uuid is not None:
            args['uuid'] = uuid

        super().__init__(**args)

        self.properties['api_url'] = self.api_url_external

        self.thread_stop = threading.Event()
        self.thread = threading.Thread(target=self.reconcile_periodically)
        self.thread.start()

    def reconcile_periodically(self):
        while not self.thread_stop.wait(2):
            self.reconcile()

    def get_uuid(self):
        try:
            r = requests.get(self.api_url)
            r.raise_for_status()
            return r.json().get('uuid')
        except requests.exceptions.RequestException:
            return None

    def get_status(self):
        try:
            r = requests.get(self.api_url)
            r.raise_for_status()

            return r.json()

        except requests.exceptions.RequestException:
            self.change_state('error', error='Failed to contact VILLASrelay')

            return None

    def reconcile(self):
        status = self.get_status()
        if status is None:
            return

        if self._state == 'error':
            self.change_state('idle')

        self._status = status
        self._version = self._status['version']

        active_sessions = self._status['sessions']
        active_uuids = {session['uuid'] for session in active_sessions}
        existing_uuids = set(self.components.keys())

        # Add new sessions and update existing ones
        for session in active_sessions:
            uuid = session['uuid']

            if uuid in self.components:
                comp = self.components[uuid]

                comp.change_state('running')
            else:
                comp = VILLASrelayGateway(self, session)

                self.add_component(comp)

        # Find vanished sessions
        for uuid in existing_uuids - active_uuids:
            comp = self.components[uuid]

            self.remove_component(comp)

        if len(self.components) > 0:
            self.change_state('running')
        else:
            self.change_state('paused')

    @property
    def status(self):
        return {
            'villas_relay_version': self._version,
            **super().status
        }

    def on_shutdown(self):
        self.thread_stop.set()
        self.thread.join()

        return super().on_shutdown()

    def on_ready(self):
        if self.autostart:
            os.system('villas-relay')

        try:
            status = self.get_status()

            self._version = status['version']

        except Exception:
            self.change_state('error', error='Failed to contact VILLASrelay')

        super().on_ready()
