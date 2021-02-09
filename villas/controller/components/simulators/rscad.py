import socket
import time

from villas.controller.components.simulator import Simulator


class RscadSimulator(Simulator):

    def __init__(self, host, number):
        raise NotImplementedError()

        # Rack.__init__(self, host, number)

        self.name = f'{host}({number})'

    @property
    def state(self):
        try:
            user, case = self.ping()

            if len(user) > 0:
                state = {
                    'status': 'running',
                    'user': user,
                    'case': case
                }
            else:
                state = {
                    'status': 'free'
                }
        except socket.timeout:
            state = {
                'status': 'offline'
            }

        state['time'] = int(round(time.time() * 1000))

        return state
