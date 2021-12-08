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

        self.thread_stop = threading.Event()
        self.thread = threading.Thread(target=self.reconcile_periodically)

        uuid = self.get_uuid()
        if uuid is not None:
            args['uuid'] = uuid

        super().__init__(**args)

        self.properties['api_url'] = self.api_url_external

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
            self.change_to_error('Failed to contact VILLASrelay')

            return None

    def reconcile_periodically(self):
        while not self.thread_stop.wait(2):
            self.reconcile()

    def reconcile(self):
        try:
            self._status = self.get_status()

            active_sessions = self._status['sessions']
            active_uuids = {session['uuid'] for session in active_sessions}
            existing_uuids = set(self.components.keys())

            # Add new sessions and update existing ones
            for session in active_sessions:
                uuid = session['uuid']

                if uuid in self.components:
                    comp = self.components[uuid]
                else:
                    comp = VILLASrelayGateway(self, session)
                    self.add_component(comp)

                comp.change_state('running')

            # Find vanished sessions
            for uuid in existing_uuids - active_uuids:
                comp = self.components[uuid]

                comp.change_state('stopped')

                # We dont remove the components here
                # So that they dont get removed from the backend
                # and get recreated with the same UUID later
                # self.remove_component(comp)

            if len(active_sessions) > 0:
                self.change_state('running')
            else:
                self.change_state('paused')

        except Exception as e:
            self.change_to_error('failed to reconcile',
                                 exception=str(e),
                                 args=e.args)

    @property
    def status(self):
        status = super().status

        status['status']['villas_relay_version'] = self._status.get('version')

        return status

    def on_shutdown(self):
        self.thread_stop.set()
        self.thread.join()

        return super().on_shutdown()

    def on_ready(self):
        if self.autostart:
            os.system('villas-relay')

        self.thread.start()

        super().on_ready()
