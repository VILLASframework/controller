#!/usr/bin/env python
import logging
import pika
import json
import config
import time

import villas.controller as controller
import villas.amqp as amqp

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
			  '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

def main():
	logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

	connection = amqp.Connection(config.BROKER_URI)
	chan = connection.channel()
	
	simulator = controller.RscadSimulator(config.SIM_HOST, config.SIM_RACK_NUMBER)
	
	pub = controller.StatusPublisher(chan)
	sub = controller.StatusSubscriber(chan)

	try:
		conn.run()
	except KeyboardInterrupt:
		conn.stop()
	
	LOGGER.info("Goodbye!")

if __name__ == '__main__':
	main()