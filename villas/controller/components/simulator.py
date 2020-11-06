import uuid
import time
import os
import requests
import io
import tempfile
import zipfile

from villas.controller.component import Component
from villas.controller.exceptions import SimulationException
from villas.controller.simulators import dummy, generic, rtlab, rscad, dpsim


class Simulator(Component):

    def __init__(self, **args):
        super().__init__(**args)

        self.model = None
        self.results = None

    @property
    def state(self):
        return {
            'model': self.model,
            'results': self.results,

            **super().state
        }

    @staticmethod
    def from_json(json):
        if json['type'] == 'dummy':
            return dummy.DummySimulator(**json)
        if json['type'] == 'generic':
            return generic.GenericSimulator(**json)
        elif json['type'] == 'dpsim':
            return dpsim.DPsimSimulator(**json)
        elif json['type'] == 'rtlab':
            return rtlab.RTLabSimulator(**json)
        elif json['type'] == 'rscad':
            return rscad.RSCADSimulator(**json)
        else:
            return None

    def change_state(self, state, force=False, **kwargs):
        if self._state == state:
            return

        valid_state_transitions = {
            # current       # list of valid next states
            'error':        ['resetting', 'error'],
            'idle':         ['resetting', 'error', 'idle', 'starting',
                             'shuttingdown'],
            'starting':     ['resetting', 'error', 'running'],
            'running':      ['resetting', 'error', 'pausing', 'stopping'],
            'pausing':      ['resetting', 'error', 'paused'],
            'paused':       ['resetting', 'error', 'resuming', 'stopping'],
            'resuming':     ['resetting', 'error', 'running'],
            'stopping':     ['resetting', 'error', 'idle'],
            'resetting':    ['resetting', 'error', 'idle'],
            'shuttingdown': ['shutdown', 'error'],
            'shutdown':     ['starting', 'error']
        }

        # check that we have been asked for a valid state
        if state not in valid_state_transitions:
            raise SimulationException(self, msg='Invalid state', state=state)

        if not force and state not in valid_state_transitions[self._state]:
            raise SimulationException(self, msg='Invalid state transtion',
                                      current=self._state, next=state)

        self._state = state
        self._stateargs = kwargs

        self.logger.info('Changing state to %s', state)

        if 'msg' in kwargs:
            self.logger.info('Message is: %s', kwargs['msg'])

        if state == 'stopping':
            self.upload_results()

        self.publish_state()

    # Actions
    def start(self, message):
        self.started = time.time()
        self.simuuid = uuid.uuid4()

        if 'parameters' in message.payload:
            self.params = message.payload['parameters']

        if 'model' in message.payload:
            self.model = message.payload['model']

        if 'results' in message.payload:
            self.results = message.payload['results']

        self.workdir = '/var/villas/controller/simulators/' + \
            str(self.uuid) + '/simulation/' + str(self.simuuid)

        self.logdir = self.workdir + '/Logs/'
        self.logger.info('Target working directory: %s' % self.workdir)

        try:
            os.makedirs(self.logdir)
            os.chdir(self.logdir)
        except Exception as e:
            raise SimulationException(self, 'Failed to create and change to '
                                            'working directory: %s ( %s )' %
                                            (self.logdir, e))

    def _upload(self, filename):
        with open(filename, 'rb') as f:
            with requests.put(self.results['url'], body=f) as r:
                self.logger.info(f'Uploaded file {filename} to {url}')

    def _download(self, url):
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xml') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)

                return f.name

    def _zip_files(self, folder):
        pass

    def _unzip_files(self, filename):
        if filename is not None:
            if zipfile.is_zipfile(filename):
                with zipfile.ZipFile(filename, 'r') as zip_ref:
                    zipdir = tempfile.mkdtemp()
                    zip_ref.extractall(zipdir)
                    return zipdir
            else:
                return filename

    def upload_results(self):
        try:
            filename = self.workdir + '/results.zip'
            with zipfile.ZipFile(filename, 'w') as results_zip:
                for sub in os.scandir(self.logdir):
                    results_zip.write(sub)

                results_zip.close()

        except Exception as e:
            self.logger.error('Zip failed: %s', e)

        if 'url' in self.results:
            self._upload(filename)
        else:
            self.logger.info('No URL provided for result upload. '
                             'Skipping upload.')

    def download_model(self):
        if self.model:
            if 'url' in self.model:
                filename = self._download(self.model['url'])

                return self._unzip_files(filename)
            else:
                self.logger.info('No URL provided for model download. '
                                 'Skipping download.')
