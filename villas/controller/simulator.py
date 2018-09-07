import logging
import kombu
import uuid
import time
import socket
import os
import pycurl
import io
import tempfile
import zipfile

from .exceptions import SimulationException
from . import __version__ as version

from .exceptions import SimulationException
from . import __version__ as version
import pycurl

class Simulator(object):

	def __init__(self, **args):
		self.realm = args['realm']
		self.type = args['type']
		self.name = args['name']
		self.enabled = args['enabled'] if 'enabled' in args else True
		self.uuid = args['uuid'] if 'uuid' in args else uuid.uuid4()
		self.started = time.time()

		self.properties = args

		self.model = None
		self._state = 'idle'
		self._stateargs = {}

		self.logger = logging.getLogger("villas.controller.simulator:" + self.uuid)

		self.exchange = kombu.Exchange(
			name = 'villas',
			type = 'headers',
			durable = True
		)
		try:
			self.uuid = args['uuid'] if 'uuid' in args else uuid.uuid4()
		except Exception as e:
			self.logger = logging.getLogger("villas.controller.simulator:")
			self.logger.info(e.msg)
		self.logger = logging.getLogger("villas.controller.simulator:" + self.uuid)

	def set_connection(self, connection):
		self.connection = connection

		self.producer = kombu.Producer(
			channel = self.connection.channel(),
			exchange = self.exchange
		)

		self.publish_state()

	@staticmethod
	def from_json(json):
		from .simulators import dummy, generic, rtlab, rscad

		if json['type'] == "dummy":
			return dummy.DummySimulator(**json)
		if json['type'] == "generic":
			return generic.GenericSimulator(**json)
		elif json['type'] == "dpsim":
			from .simulators import dpsim
			return dpsim.DPsimSimulator(**json)
		elif json['type'] == "rtlab":
			return dpsim.RTLabSimulator(**json)
		elif json['type'] == "rscad":
			return dpsim.RSCADSimulator(**json)
		else:
			return None

	def get_consumer(self, channel):
		self.channel = channel

		return kombu.Consumer(
			channel = self.channel,
			on_message = self.on_message,
			queues = kombu.Queue(
				exchange = self.exchange,
				binding_arguments = self.headers,
				durable = False
			),
			no_ack = True,
			accept = {'application/json'}
		)

	@property
	def headers(self):
		return {
			'x-match' : 'any',
			'category' : 'simulator',
			'realm' : self.realm,
			'uuid' : self.uuid,
			'type' : self.type
		}

	@property
	def state(self):
		state = {
			'state' : self._state,
			'model' : self.model,
			'version' : version,
			'properties' : self.properties,
			'uptime' : time.time() - self.started,
			'host' : socket.getfqdn(),
			'kernel' : os.uname(),

			**self._stateargs
		}

		return state

	def on_message(self, message):
		self.logger.debug('Received message: %s', message.payload)

		if 'action' in message.payload:
			self.run_action(message.payload['action'], message)

	def run_action(self, action, message):
		self.logger.info('Received %s command', action)

		try:
			if action == 'ping':
				self.ping(message)
			elif action == 'start':
				self.change_state('starting')
				self.start(message)
			elif action == 'stop':
				# state changed to stopping after the simulation
				# has ended, to avoid missing log entries
				self.stop(message)
			elif action == 'pause':
				self.change_state('pausing')
				self.pause(message)
			elif action == 'resume':
				self.change_state('resuming')
				self.resume(message)
			elif action == 'shutdown':
				self.change_state('shuttingdown')
				self.shutdown(message)
			elif action == 'reset':
				self.change_state('resetting')
				self.reset(message)
			else:
				raise SimulationException(self, 'Unknown action', action = action)
		except SimulationException as se:
			self.change_state('error', msg = se.msg, **se.info)
		finally:
			message.ack()

	def publish_state(self):
		self.producer.publish(
			self.state,
			headers = self.headers
		)

	def change_state(self, state, **kwargs):
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
			'shuttingdown' : [ 'shutdown' ]
		}

		# check that we have been asked for a valid state
		if state not in valid_state_transitions:
			raise SimulationException(self, msg = 'Invalid state', state = state)

		if state not in valid_state_transitions[self._state]:
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
	def ping(self, message):
		self.publish_state()

	def start(self, message):
		self.started = time.time()
		self.simuuid = uuid.uuid4();
		if 'parameters' in message.payload:
			self.params = message.payload['parameters']
		if 'model' in message.payload:
			self.model = message.payload['model']
		if 'results' in message.payload:
			self.results = message.payload['results']
		self.workdir = "/var/villas/controller/simulators/" + \
			str(self.uuid) + "/simulation/" + str(self.simuuid);
		self.logdir = self.workdir + "/Logs/"
		self.logger.info("Target working directory: %s" % self.workdir)
		try:
			os.makedirs(self.logdir)
			os.chdir(self.logdir)
		except Exception as e:
			raise SimulationException(self, 'Failed to create and change to working directory: %s ( %s )' % (self.logdir, e))

	def stop(self, message):
		pass

	def pause(self, message):
		pass

	def resume(self, message):
		pass

	def shutdown(self, message):
		pass

	def reset(self, message):
		self.started = time.time()

	def pycurl_upload(self, filename):
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

	def upload_results(self):
		try:
			filename = self.workdir + '/results.zip'
			with zipfile.ZipFile(filename, 'w') as results_zip:
				for sub in os.scandir(self.logdir):
					results_zip.write(sub);
				results_zip.close();

		except Exception as e:
			self.logger.error('Zip failed: %s' % str(e))

		if 'url' in self.results:
			self.pycurl_upload(filename)

	def writeBufferToTemporaryFile(self, buf):
		if buf != None:
			try:
				fp = tempfile.NamedTemporaryFile(delete=False, suffix=".xml")
				fp.write(buf.getvalue())
				fp.close()
				return fp.name
			except IOError as e:
				self.logger.error('Failed to process url: ' + url + ' in temporary file: ' + fp.name + str(e))
		return None

	def unzipFile(self, filename):
		if filename is not None:
			if zipfile.is_zipfile(filename):
				with zipfile.ZipFile(filename,"r") as zip_ref:
					zipdir = tempfile.mkdtemp()
					zip_ref.extractall(zipdir)
					return zipdir
			else:
				return filename

	def check_download(self, message):
		self.logger.info(self.model)
		if self.model:
			if 'url' in self.model:
				buf = self.downloadURL(self.model['url'])
				filename = self.writeBufferToTemporaryFile(buf)
				return self.unzipFile(filename)
			else:
				self.logger.info("No url in message.properties['application_headers']:")
				self.logger.info(message.properties['application_headers'])

	def downloadURL(self, url):
		try:
			buffer = io.BytesIO()
			c = pycurl.Curl()
			c.setopt(c.URL, url)
			c.setopt(c.WRITEDATA, buffer)
			c.perform()
			c.close()
		except pycurl.error as e:
			self.logger.error('Failed to load url: ' + url + " error: " + str(e))
			return None

		return buffer

	def __str__(self):
		return "%sSimulator <%s: %s>" % (self.type, self.name, self.uuid)
