#!/usr/bin/env python

import sys
import logging
import argparse
import config
import uuid
import socket
import time

from kombu import Connection, Queue, Producer, Consumer, Exchange, uuid

LOGGER = logging.getLogger(__name__)

class DiscoveryRPC(object):
	def __init__(self, connection):
		self.connection = connection
		
		self.exchange = Exchange(
			channel = connection,
			name = 'discover',
			durable = True
		)
		
		self.queue = Queue(
			channel = connection,
			routing_key = uuid(),
			exchange = self.exchange,
			exclusive = True
		)

	def on_response(self, message):
		if message.properties['correlation_id'] == self.correlation_id:
			self.response.append(message.payload)

	def call(self):
		self.response = [ ]
		self.correlation_id = uuid()
		
		with Producer(self.connection) as producer:
			producer.publish(
				body = { },
				exchange       = self.exchange,
				reply_to       = self.queue.routing_key,
				correlation_id = self.correlation_id
			)

		with Consumer(self.connection, on_message = self.on_response, queues = [ self.queue ], no_ack = True):
			while True:
				try:
					self.connection.drain_events(timeout = 2)
				except socket.timeout:
					break

		return self.response

def cmd_disco(c, args):
	rpc = DiscoveryRPC(c)
	
	targets = rpc.call()
	
	for target in targets:
		print target

def cmd_monitor(connection, args):
	pass

def setup_logging():
	logging.basicConfig(level=logging.DEBUG)

	LOGGER.setLevel(logging.DEBUG)

def setup_argparse():
	# Main parser
	parser = argparse.ArgumentParser(prog = 'villasctl')
	parser.add_argument('--broker',
		help='URL of AMQP broker',
		default = config.BROKER_URI
	)
	
	subparsers = parser.add_subparsers(help = 'Available subcommands:')
	
	# Discovery subcommand
	disco_parser = subparsers.add_parser('discover', help='Discover targets')
	disco_parser.set_defaults(func = cmd_disco)
	disco_parser.add_argument('--type',
		help='Limit to a special type',
		default = '*'
	)

	# Monitor subcommand
	monitor_parser = subparsers.add_parser('monitor', help='Listen to events')
	monitor_parser.set_defaults(func = cmd_monitor)

	return parser
	
def main():
	setup_logging()
	parser = setup_argparse()
	
	args = parser.parse_args(sys.argv[1:])
	
	with Connection(args.broker) as c:
		try:
			args.func(c, args)
		except KeyboardInterrupt:
			LOGGER.info("Ctrl-C... Abort")

if __name__ == '__main__':
	main()
