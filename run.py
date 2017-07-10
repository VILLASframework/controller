#!/usr/bin/env python
import logging
import pika
import json
import config
import time

import villas.controller as controller
import villas.amqp as amqp

simulators = [
	controller.RscadSimulator('134.130.40.72', 4)
]

def connected(connection):
	handles = [
		controller.StatusPublisher(connection, simulator) for simulator in simulators,
		controller.StatusConsumer(connection)
	]

def main():
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)
	
	logger2 = logging.getLogger('pika.callback')
	logger2.setLevel(logging.INFO)
	
	connection = amqp.Connection(config.BROKER_URI, connected)
	
	try:
		connection.run()
	except KeyboardInterrupt:
		connection.stop()
		logger.info("Goodbye!")

if __name__ == '__main__':
	main()