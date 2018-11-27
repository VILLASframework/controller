import logging
import uuid
import time
import os
import pycurl
import io
import tempfile
import zipfile

from ..component import Component
from ..exceptions import SimulationException

class Simulator(Component):

	def __init__(self, **args):
		super().__init__(**args)

		self.model = None
		self.results = None

	@property
	def state(self):
		return {
			'model' : self.model,
			'results' : self.results,

			**super().state
		}

	@staticmethod
	def from_json(json):
		from .simulators import dummy, generic, rtlab, rscad

		if json['type'] == 'dummy':
			return dummy.DummySimulator(**json)
		if json['type'] == 'generic':
			return generic.GenericSimulator(**json)
		elif json['type'] == 'dpsim':
			from .simulators import dpsim
			return dpsim.DPsimSimulator(**json)
		elif json['type'] == 'rtlab':
			return dpsim.RTLabSimulator(**json)
		elif json['type'] == 'rscad':
			return dpsim.RSCADSimulator(**json)
		else:
			return None

	def change_state(self, state, force=False, **kwargs):
		if self._state == state:
			return

		valid_state_transitions = {
			# current        # list of valid next states
			'error':         [ 'resetting', 'error' ],
			'idle':          [ 'resetting', 'error', 'idle', 'starting', 'shuttingdown' ],
			'starting':      [ 'resetting', 'error', 'running' ],
			'running':       [ 'resetting', 'error', 'pausing', 'stopping' ],
			'pausing':       [ 'resetting', 'error', 'paused' ],
			'paused':        [ 'resetting', 'error', 'resuming', 'stopping' ],
			'resuming':      [ 'resetting', 'error', 'running' ],
			'stopping':      [ 'resetting', 'error', 'idle' ],
			'resetting' :    [ 'resetting', 'error', 'idle' ],
			'shuttingdown' : [ 'shutdown', 'error' ],
			'shutdown' :     [ 'starting', 'error' ]
		}

		# check that we have been asked for a valid state
		if state not in valid_state_transitions:
			raise SimulationException(self, msg = 'Invalid state', state = state)

		if not force and state not in valid_state_transitions[self._state]:
			raise SimulationException(self, msg = 'Invalid state transtion', current = self._state, next = state)

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
			raise SimulationException(self, 'Failed to create and change to working directory: %s ( %s )' % (self.logdir, e))

	def _pycurl_upload(self, filename):
		try:
			c = pycurl.Curl()
			url = self.results['url']
			c.setopt(pycurl.URL, url)
			c.setopt(pycurl.UPLOAD, 1)
			c.setopt(pycurl.READFUNCTION, open(filename, 'rb').read)
			filesize = os.path.getsize(filename)
			c.setopt(pycurl.INFILESIZE, filesize)
			self.logger.info('Uploading %d bytes of file %s to url %s' % (filesize, filename, url))
			c.perform()
			c.close()

		except Exception as e:
			self.logger.error('Curl failed: %s' % str(e))

	def _pycurl_download(self, url):
		try:
			buffer = io.BytesIO()
			c = pycurl.Curl()
			c.setopt(c.URL, url)
			c.setopt(c.WRITEDATA, buffer)
			c.perform()
			c.close()

			fp = tempfile.NamedTemporaryFile(delete = False, suffix = '.xml')
			fp.write(buffer.getvalue())
			fp.close()

		except pycurl.error as e:
			self.logger.error('Failed to load url: ' + url + ' error: ' + str(e))
			return None
		except IOError as e:
			self.logger.error('Failed to process url: ' + url + ' in temporary file: ' + fp.name + str(e))
			return None
		finally:
			return fp.name

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
			self.logger.error('Zip failed: %s' % str(e))

		if 'url' in self.results:
			self._pycurl_upload(filename)
		else:
			self.logger.info('No URL provided for result upload. Skipping upload.')

	def download_model(self):
		if self.model:
			if 'url' in self.model:
				filename = self._pycurl_download(self.model['url'])

				return self._unzip_files(filename)
			else:
				self.logger.info('No URL provided for model download. Skipping download.')
