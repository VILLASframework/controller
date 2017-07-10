import logging
import pika

LOGGER = logging.getLogger(__name__)

class Connection(pika.SelectConnection):

	def __init__(self, amqp_url, on_open_callback):
		LOGGER.info('Connecting to %s' % amqp_url)
		
		self.on_open_callback = on_open_callback
		
		super(self.__class__, self).__init__(
			parameters = pika.connection.URLParameters(amqp_url),
			on_open_callback = self.on_open,
			stop_ioloop_on_close = False
		)

	def run(self):
		self.ioloop.start()
		
	def stop(self):
		# Gracefully close the connection
		self.close()
		
		# Start the IOLoop again so Pika can communicate, it will stop on its own when the connection is closed
		self.ioloop.start()

	def on_open(self, unused_connection):
		LOGGER.info('Connection opened')
		
		self.on_open_callback(self)

		self.add_on_close_callback(self.on_closed)

	def on_closed(self, connection, reply_code, reply_text):
		LOGGER.info('Connection closed')

		self.ioloop.stop()

#			LOGGER.warning('Connection closed, reopening in 5 seconds: (%s) %s', reply_code, reply_text)
#			self.add_timeout(5, self.reconnect)

	def reconnect(self):
		# This is the old connection IOLoop instance, stop its ioloop
		self.ioloop.stop()
		
		LOGGER.info('Reconnect')

		if not self.is_closing:
			# Create a new connection
			self.connect()

			# There is now a new connection, needs a new ioloop to run
			self.ioloop.start()
