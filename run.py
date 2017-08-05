#!/usr/bin/env python
import logging
import config
import time

from kombu import Connection, Queue
from kombu.mixins import ConsumerMixin
from kombu.pools import connections

import villas.controller as controller

class Worker(ConsumerMixin):

	def __init__(self, channel):
		self.connection = channel
		
	def get_consumers(self, Consumer, channel):
		return [
			controller.StatusConsumer(channel),
			controller.Discovery(channel, simulators)
		]

simulators = [ 
	controller.RscadSimulator('134.130.40.72', 2),
	controller.RscadSimulator('134.130.40.73', 3),
	controller.RscadSimulator('134.130.40.74', 4),
	controller.RscadSimulator('134.130.40.75', 5),
	controller.RscadSimulator('134.130.40.76', 6),
	controller.RscadSimulator('134.130.40.77', 7),
]

if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)

	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	
	logger3 = logging.getLogger('rtds')
	logger3.setLevel(logging.INFO)

	c = Connection(config.BROKER_URI)
	w = Worker(c)
	
	publishers = [ controller.StatusPublisher(c.clone(), s) for s in simulators ]
	
	try:
		w.run()
	except KeyboardInterrupt:
		pass
	
	logger.info('Shutdown')
	map(lambda x: x.cancel(), publishers)