import logging
import threading

from kombu import Producer, Exchange

LOGGER = logging.getLogger(__name__)

class Timer(threading.Thread):
	def __init__(self, interval):
		super(Timer, self).__init__()
	
		self.interval = interval
		self.event = threading.Event()

	def run(self):
		while not self.stopped():
			self.periodical()
			self.event.wait(self.interval)
		
		LOGGER.info("Thread stopped")
	
	def stopped(self):
		return self.event.is_set()

	def cancel(self):
		LOGGER.info('Stopping thread: %s', threading.current_thread)
		self.event.set()
		self.join()

class StatusPublisher(Producer, Timer):

	def __init__(self, channel, simulator):
		LOGGER.info('Starting status publisher for %s with connection %s', simulator, channel)

		Timer.__init__(self,
			interval = 2.0
		)
		
		Producer.__init__(self,
			channel = channel,
			exchange = Exchange(
				name = 'status',
				type = 'topic',
				durable = False
			),
			routing_key = 'status.simulator.rtds.rack1'
		)
		
		self._simulator = simulator
		
		self.start()
	
	def periodical(self):
		state = {
			'state' : self._simulator.state,
			'name'	:  self._simulator.name
		}
		
		self.publish(state)