import logging
import pika

LOGGER = logging.getLogger(__name__)
	
class Channel(object):
	def __init__(self, connection):
		LOGGER.info('Creating a new channel')
		
		self._connection = connection		
		self._connection.channel(on_open_callback = self.on_open)

	def on_open(self, channel):
		LOGGER.info('Channel opened')

		self._channel = channel
		self._channel.add_on_close_callback(self.on_closed)

	def on_closed(self, channel, reply_code, reply_text):
		LOGGER.info('Channel %i was closed: (%s) %s', channel, reply_code, reply_text)

		self._connection.close()