import uuid
import time
import os
import requests
import tempfile
import zipfile

from villas.controller.component import Component
from villas.controller.exceptions import SimulationException


class Simulator(Component):

    def __init__(self, **args):
        super().__init__(**args)

        self.model = None
        self.t_up_token = None
        self.t_down_token = None
        self.results = None

    @property
    def status(self):
        return {
            'model': self.model,
            'results': self.results,

            **super().status
        }

    @staticmethod
    def from_dict(dict):
        type = dict.get('type')

        if type == 'dummy':
            from villas.controller.components.simulators import dummy
            return dummy.DummySimulator(**dict)
        if type == 'generic':
            from villas.controller.components.simulators import generic
            return generic.GenericSimulator(**dict)
        elif type == 'dpsim':
            from villas.controller.components.simulators import dpsim
            return dpsim.DPsimSimulator(**dict)
        elif type == 'rtlab':
            from villas.controller.components.simulators import rtlab
            return rtlab.RTLabSimulator(**dict)
        elif type == 'rscad':
            from villas.controller.components.simulators import rscad
            return rscad.RSCADSimulator(**dict)
        else:
            return None

    def change_state(self, state, force=False, **kwargs):
        if self._state == state:
            return

        valid_state_transitions = {
            # current       # list of valid next states
            'error':        ['resetting', 'error', 'gone'],
            'idle':         ['resetting', 'error', 'idle', 'starting',
                             'shuttingdown', 'gone'],
            'starting':     ['resetting', 'error', 'running', 'gone'],
            'running':      ['resetting', 'error', 'pausing',
                             'stopping', 'gone'],
            'pausing':      ['resetting', 'error', 'paused', 'gone'],
            'paused':       ['resetting', 'error', 'resuming',
                             'stopping', 'gone'],
            'resuming':     ['resetting', 'error', 'running', 'gone'],
            'stopping':     ['resetting', 'error', 'idle', 'gone'],
            'resetting':    ['resetting', 'error', 'idle', 'gone'],
            'shuttingdown': ['shutdown', 'error', 'gone'],
            'shutdown':     ['starting', 'error', 'gone'],
            'gone':         []
        }

        # check that we have been asked for a valid state
        if state not in valid_state_transitions:
            raise SimulationException(self, msg='Invalid state', state=state)

        if not force and state not in valid_state_transitions[self._state]:
            raise SimulationException(self, msg='Invalid state transtion',
                                      current=self._state, next=state)

        self.logger.info('Changing state to %s', state)

        if 'msg' in kwargs:
            self.logger.info('Message is: %s', kwargs['msg'])

        super().change_state(state, **kwargs)

    # Actions
    def start(self, payload):
        self.started = time.time()
        self.simuuid = uuid.uuid4()

        self.params = payload.get('parameters', {})
        self.model = payload.get('model')
        self.t_down_token = self.model.get('token',None)
        
        self.results = payload.get('results')
        self.t_up_token = self.results.get('token',None)
        try:
            del self.results['token']
            del self.model['token']
        except:
            pass

        self.sim_workdir = os.path.join(self.workdir, 'simulation',
                                        str(self.simuuid))

        self.sim_logdir = self.sim_workdir + '/logs/'
        self.logger.info('Simulation working directory: %s' % self.sim_workdir)

        try:
            os.makedirs(self.sim_workdir)
            os.chdir(self.sim_workdir)
        except Exception as e:
            raise SimulationException(self, 'Failed to create and change to '
                                            'working directory: %s ( %s )' %
                                            (self.sim_logdir, e))

    def _upload(self, filename):
        url = self.results['url']
        params={"url":url}
        if self.t_up_token:
            params["headers"] = {"Authorization":f"Bearer {self.t_up_token}"}
            self.t_up_token = None
        with open(filename, 'rb') as f:
            params["files"] = {'file':f}
            r = requests.post(**params)
            r.raise_for_status()
            self.logger.info(f'Uploaded file {filename} to {url}')

    def _download(self, url):
        params = {"url":url,"stream":True}
        if self.t_down_token:
            params["headers"] = {"Authorization":f"Bearer {self.t_down_token}"}
            self.t_down_token = None
        with requests.get(**params) as r:
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
            filename = os.path.join(self.sim_workdir, 'results.zip')
            with zipfile.ZipFile(filename, 'w') as results_zip:
                for sub in os.scandir(self.sim_logdir):
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
