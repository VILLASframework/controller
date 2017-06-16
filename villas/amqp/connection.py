import logging
import pika

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

class Connection(pika.SelectConnection):

	def __init__(self, amqp_url):
		self._url = amqp_url
		
		LOGGER.info('Connecting to %s', self._url)
		
		pika.SelectConnection(self,
			parameters =  pika.URLParameters(self._url),
            on_open_callback = self.on_connection_open,
            stop_ioloop_on_close = False
		)

    def on_open(self, unused_connection):
        LOGGER.info('Connection opened')
        self.add_on_close_callback(self.on_connection_closed)
        
		self._channel = Channel(self)

    def on_closed(self, connection, reply_code, reply_text):
        self._channel = None
        if self._closing:
            self.ioloop.stop()
        else:
            LOGGER.warning('Connection closed, reopening in 5 seconds: (%s) %s', reply_code, reply_text)
            self.add_timeout(5, self.reconnect)

    def reconnect(self):
        # This is the old connection IOLoop instance, stop its ioloop
        self.ioloop.stop()

        if not self.is_closing:
            # Create a new connection
            self.connect()

            # There is now a new connection, needs a new ioloop to run
            self.ioloop.start()
