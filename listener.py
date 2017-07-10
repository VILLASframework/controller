#!/usr/bin/env python
import pika
import json
import config

def callback(channel, method, properties, body):
	json_body = json.loads(body)

	print("Received %r" % json_body)

def main():
	logging.basicConfig(level=logging.DEBUG, format=LOG_FORMAT)

	parameters = pika.URLParameters(config.BROKER_URL)
	connection = pika.BlockingConnection(parameters)
	channel = connection.channel()
	exchange = channel.exchange_declare(exchange='status', type='topic')
	queue = channel.queue_declare(queue='', exclusive=True)

	channel.queue_bind(
		exchange='status',
		queue=queue.method.queue,
		routing_key='status.simulator.#'
	)

	channel.basic_consume(
		callback,
		queue=queue.method.queue,
		no_ack=True
	)

	channel.start_consuming()
	connection.close()

if __name__ == '__main__':
	main()
