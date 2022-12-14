import os
import sys
import threading
import re
import psutil
import subprocess
import signal

from villas.controller.exceptions import SimulationException
from villas.controller.components.simulator import Simulator


class GenericSimulator(Simulator):

    def __init__(self, **args):
        super().__init__(**args)

        self.child = None
        self.return_code = None
        self.timer = None
        self.thread = None

    def __del__(self):
        if self.timer:
            self.timer.cancel()

    @property
    def status(self):
        status = super().status

        status['status']['return_code'] = self.return_code

        return status

    def start(self, payload):
        super().start(payload)
        self.logger.info('Working directory: %s', os.getcwd())
        path = self.download_model()

        # Start an external command
        if self.child is not None:
            raise SimulationException(self, 'Child process is already running')

        try:
            params = payload['parameters']

            self.thread = threading.Thread(target=GenericSimulator.run,
                                           args=(self, params, path))
            self.thread.start()
        except Exception as e:
            raise SimulationException(self,
                                      msg='Failed to start child process: '
                                      + e)

    def check_state(self, state):
        if self._state != state:
            self.change_to_error('Failed to transition to state', state=state)

    def check_state_deferred(self, state, timeout=5):
        self.timer = threading.Timer(timeout, self.check_state, args=[state])
        self.timer.start()

    def run(self, params, path):
        try:
            args = {}
            argv0 = params['executable']
            argv = [argv0]

            if 'argv' in params:
                # Substitute the path location into the command if necessary
                if path is not None:
                    argv += [str(x).replace('%PATH%', path) for
                             x in params['argv']]
                else:
                    argv += [str(x) for x in params['argv']]

            if 'shell' in params:
                if ('shell' not in self.properties or
                        not self.properties['shell']):
                    raise SimulationException(self, 'Shell execution '
                                              'is not allowed!')
                args['shell'] = params['shell']

            if 'working_directory' in params:
                args['cwd'] = params['working_directory']

            if 'environment' in params:
                args['env'] = params['shell']

            valid = False
            if 'whitelist' in self.properties:
                for regex in self.properties['whitelist']:
                    self.logger.info('Checking for match: %s', regex)
                    if re.match(regex, argv0) is not None:
                        valid = True
                        break

            if not valid:
                raise SimulationException(self, 'Executable is not whitelisted'
                                          ' for this simulator',
                                          executable=argv0)

            self.logger.info('Execute: %s', argv)
            logfile = None
            if 'stdout_logfile' in params:
                logfile = open(self.params['stdout_logfile'], 'w')
                self.child = subprocess.Popen(argv, **args,
                                              stdout=logfile,
                                              stderr=subprocess.STDOUT)
            else:
                self.child = subprocess.Popen(argv, **args,
                                              stdout=sys.stdout,
                                              stderr=subprocess.STDOUT)

            self.change_state('running')

            self.child.wait()
            if logfile is not None:
                logfile.close()
            if self.child.returncode == 0:
                self.logger.info('Child process has finished.')
                self.change_state('stopping')
                self.upload_results()
                self.change_state('idle')
            elif self.child.returncode > 0:
                self.return_code = self.child.returncode
                raise SimulationException(self, 'Child process exited',
                                          code=self.return_code)
            elif self.child.returncode == -signal.SIGTERM:
                self.logger.info('Child process was terminated successfully')
                self.change_state('idle')
            elif (self.child.returncode == -signal.SIGKILL and
                  self._state == 'resetting'):
                self.logger.info('Child process was resetted successfully')
                self.change_state('idle')
            else:
                sig = signal.Signals(-self.child.returncode)
                raise SimulationException(self, 'Child process caught signal',
                                          signal=-self.child.returncode,
                                          signal_name=sig.name)

        # GenericSimulator.run() is executed in a separate thread.
        # We therefore want to catch exceptions here.
        except SimulationException as se:
            self.change_to_error(se.msg, **se.info)

        self.child = None

    def reset(self, payload):
        # Don't send a signal if the child does not exist
        if self.child is None:
            return

        # Kill all childs of the simulation process
        parent = psutil.Process(self.child.pid)
        children = parent.children(recursive=True)

        for child in children:
            child.kill()

        parent.kill()

        # Stop the external command (kill)
        # This is a hard reset!
        self.child.send_signal(signal.SIGKILL)

        # Final transition to idle state occurs in run thread
        # If this transition does not occur within 5 seconds,
        # we will transition into the error state
        self.check_state_deferred('idle', 5)

    def stop(self, payload):
        send_cont = False

        if self.child is None:
            raise SimulationException(self, 'No child process is running')

        if self._state == 'paused':
            send_cont = True

        # Stop the external command (SIGTERM)
        self.child.terminate()
        self.logger.info('Send termination signal to child process')

        # If the process has been paused, we must resume it
        # so that it can process the SIGTERM and exit
        if send_cont:
            self.child.send_signal(signal.SIGCONT)

        # Final transition to idle state occurs in run thread
        # If this transition does not occur within 5 seconds,
        # we will transition into the error state
        self.check_state_deferred('stopped', 5)

    def pause(self, payload):
        # Suspend command
        if self.child is None:
            raise SimulationException(self, 'No child process is running')

        self.child.send_signal(signal.SIGTSTP)

        self.change_state('paused')
        self.logger.info('Child process has been paused')

    def resume(self, payload):
        # Let process run
        if self.child is None:
            raise SimulationException(self, 'No child process is running')

        self.child.send_signal(signal.SIGCONT)

        self.change_state('running')
        self.logger.info('Child process has resumed')
