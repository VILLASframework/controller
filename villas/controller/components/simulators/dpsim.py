# SPDX-FileCopyrightText: 2014-2025 The VILLASframework Authors
# SPDX-License-Identifier: Apache-2.0

import dpsim
import os

from villas.controller.components.simulator import Simulator


class DPsimSimulator(Simulator):

    def __init__(self, **args):
        self.sim = None

        super().__init__(**args)

    @property
    def headers(self):
        headers = super().headers

        headers['type'] = 'dpsim'
        headers['version'] = '0.1.0'

        return headers

    def load_cim(self, fp):
        if fp is not None:
            self.sim = dpsim.load_cim(fp.name)
            self.logger.info(self.sim)
            os.unlink(fp.name)

    def start(self, payload):
        fp = self.download_model(payload)
        if fp:
            self.load_cim(fp)

        if self.change_state('starting'):
            self.logger.info('Starting simulation...')

            self.logger.info(self.sim)
            if self.sim.start() is None:
                self.change_state('running')
            else:
                self.change_to_error('failed to start simulation')
                self.logger.warn('Attempt to start simulator failed.'
                                 'State is %s', self._state)
        else:
            self.logger.warn('Attempted to start non-stopped simulator.'
                             'State is %s', self._state)

    def stop(self, payload):
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

    def pause(self, payload):
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

    def resume(self, payload):
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
