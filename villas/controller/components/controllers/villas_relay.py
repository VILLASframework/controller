import threading
import requests

from villas.controller.components.controller import Controller
from villas.controller.components.gateways.villas_relay import VILLASrelayGateway  # noqa E501


class VILLASrelayController(Controller):

    def __init__(self, **args):
        self.autostart = args.get('autostart', False)
        self.ws_url = args.get('api_url', 'http://localhost:8088')
        self.api_url = args.get('api_url', 'http://localhost:8088') + '/api/v1'

        self.status = self.get_status()
        self.version = self.status['version']

        args['uuid'] = self.status['uuid']

        super().__init__(**args)

        self.thread_stop = threading.Event()
        self.thread = threading.Thread(target=self.reconcile_periodically)
        self.thread.start()

    def __del__(self):
        self.thread_stop.set()
        self.thread.join()

    def reconcile_periodically(self):
        while not self.thread_stop.wait(2):
            self.reconcile()

    def get_status(self):
        r = requests.get(self.api_url)
        r.raise_for_status()

        return r.json()

    def reconcile(self):
        try:
            self.status = self.get_status()

            active_sessions = self.status['sessions']

            active_uuids = {session['uuid'] for session in active_sessions}
            existing_uuids = set(self.components.keys())

            # Add new sessions and update existing ones
            for session in active_sessions:
                uuid = session['uuid']

                if uuid in self.components:
                    ic = self.components[uuid]

                    ic.change_state('running')
                else:
                    ic = VILLASrelayGateway(self, session)

                    self.add_component(ic)

            # Find vanished sessions
            for uuid in existing_uuids - active_uuids:
                ic = self.components[uuid]

                self.remove_component(ic)

            if len(active_sessions) > 0:
                self.change_state('running')
            else:
                self.change_state('paused')

        except requests.RequestException:
            self.change_state('error', error='Failed to contact VILLASrelay')

    @property
    def state(self):
        return {
            'villas_relay_version': self.version,
            **super().state
        }

    def on_ready(self):
        try:
            r = self._api_request()

            self.version = r['version']

        except Exception:
            self.change_state('error', error='Failed to contact VILLASrelay')

        # if self.autostart:
        #   os.system('villas-relay')

        super().on_ready()
