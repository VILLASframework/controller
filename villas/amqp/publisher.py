import logging
import pika
import json

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

class Publisher(object):

	def __init__(self, channel):
		self._channel = channel
		
		self.configure()
		
	def configure(self):
		print "Configure from Pubsliher"