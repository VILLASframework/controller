import socket

from villas.controller.components.simulator import Simulator


class RscadSimulator(Simulator):

    def __init__(self, host, number):
        raise NotImplementedError()

        # Rack.__init__(self, host, number)

        self.name = f'{host}({number})'

    @property
    def status(self):
        try:
            user, case = self.ping()

            if len(user) > 0:
                status = {
                    'status': 'running',
                    'user': user,
                    'case': case
                }
            else:
                status = {
                    'status': 'free'
                }
        except socket.timeout:
            status = {
                'status': 'offline'
            }

        return {
            **super().status,
            **status
        }
