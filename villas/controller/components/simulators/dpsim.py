import dpsim
import time
import socket
import os

from villas.controller.components.simulator import Simulator


class DPsimSimulator(Simulator):

    start_schema = {
        '$schema': 'http://json-schema.org/draft-04/schema#',
        'properties': {
            'blocking': {
                'title': 'Block execution of each time-step until the '
                         'arrival of new data on the interfaces',
                'type': 'boolean'
            },
            'duration': {
                'examples': [
                    3600.0
                ],
                'title': 'Simulation duration [s]',
                'type': 'number'
            },
            'log-level': {
                'enum': ['NONE', 'INFO', 'DEBUG', 'WARN', 'ERR'],
                'title': 'Logging level',
                'type': 'string'
            },
            'name': {
                'examples': [
                    'Simulation_1'
                ],
                'title': 'Name of log files',
                'type': 'string'
            },
            'options': {
                'additionalProperties': {
                    'type': 'number'
                },
                'examples': [
                    {
                        'Ld': 0.2299,
                        'Lq': 0.0
                    }
                ],
                'title': 'User-definable options',
                'type': 'object'
            },
            'scenario': {
                'title': 'Scenario selection', 'type': 'integer'
            },
            'solver-domain': {
                'enum': ['SP', 'DP', 'EMT'],
                'title': 'Domain of solver',
                'type': 'string'
            },
            'solver-type': {
                'enum': ['NRP', 'MNA'],
                'title': 'Type of solver',
                'type': 'string'
            },
            'start-at': {
                'description': 'The date must be given as an ISO8601 '
                               'formatted string',
                'examples': ['2004-06-14T23:34:30'],
                'format': 'date-time',
                'title': 'Start time of real-time simulation',
                'type': 'string'
            },
            'start-in': {
                'title': 'Start simulation relative to current time [s]',
                'type': 'number'
            },
            'start-synch': {
                'title': 'Sychronize start of simulation '
                         'with external interfaces',
                'type': 'boolean'
            },
            'steady-init': {
                'title': 'Perform a steady-state initialization prior '
                         'to the simulation',
                'type': 'boolean'
            },
            'system-freq': {
                'examples': [
                    50.0,
                    60.0
                ],
                'title': 'System frequency [Hz]',
                'type': 'number'
            },
            'timestep': {
                'examples': [5e-05],
                'title': 'Simulation time-step [s]',
                'type': 'number'
            }
        },
        'required': ['name'],
        'type': 'object'
    }

    def __init__(self, **args):
        args['type'] = 'dpsim'

        self.started = time.time()
        self.sim = None

        super().__init__(**args)

    @property
    def headers(self):
        headers = super().headers

        headers['type'] = 'dpsim'
        headers['version'] = '0.1.0'

        return headers

    @property
    def state(self):
        state = super().state

        state['uptime'] = time.time() - self.started
        state['version'] = '0.1.0'
        state['host'] = socket.getfqdn()
        state['kernel'] = os.uname()

        return state

    def load_cim(self, fp):
        if fp is not None:
            self.sim = dpsim.load_cim(fp.name)
            self.logger.info(self.sim)
            os.unlink(fp.name)

    def start(self, message):
        fp = self.download_model(message)
        if fp:
            self.load_cim(fp)

        if self.change_state('starting'):
            self.logger.info('Starting simulation...')

            self.logger.info(self.sim)
            if self.sim.start() is None:
                self.change_state('running')
            else:
                self.change_state('error')
                self.logger.warn('Attempt to start simulator failed.'
                                 'State is %s', self._state)
        else:
            self.logger.warn('Attempted to start non-stopped simulator.'
                             'State is %s', self._state)

    def stop(self, message):
        if self._state == 'running':
            self.logger.info('Stopping simulation...')

            if self.sim and self.sim.stop() is None:
                self.change_state('stopped')
                self.logger.warn('State changed to ' + self._state)
            else:
                self.change_state('unknown')
                self.logger.warn('Attempt to stop simulator failed.'
                                 'State is %s', self._state)
        else:
            self.logger.warn('Attempted to stop non-stopped simulator.'
                             'State is %s', self._state)

    def pause(self, message):
        if self._state == 'running':
            self.logger.info('Pausing simulation...')

            self._state = 'pausing'

            try:
                if self.sim and self.sim.pause() is None:
                    self.change_state('paused')
                    self.logger.warn('State changed to ' + self._state)
                else:
                    self.logger.warn('Attempted to pause simulator failed.')
                    self.change_state('unknown')

            except SystemError as e:
                self.logger.warn('Attempted to pause simulator failed.'
                                 'Error is ' + str(e))
                self.change_state('unknown')

        else:
            self.logger.warn('Attempted to pause non-running simulator.'
                             'State is ' + self._state)

    def resume(self, message):
        if self._state == 'paused':
            self.logger.info('Resuming simulation...')

            self._state = 'resuming'

            try:
                if self.sim and self.sim.start() is None:
                    self.change_state('running')
                    self.logger.warn('State changed to %s', self._state)
                else:
                    self.logger.warn('Attempted to resume simulator failed.')
                    self.change_state('unknown')

            except SystemError as e:
                self.logger.warn('Attempted to pause simulator failed. '
                                 'Error is %s', str(e))
                self.change_state('unknown')

        else:
            self.logger.warn('Attempted to resume non-paused simulator.'
                             'State is %s', self._state)
