import os

if os.name == 'nt' and os.environ['USERDOMAIN'] == 'EONERC':
	# RabbitMQ running on OpenStack
	BROKER_URI = 'amqp://villas:n0rw4y@137.226.248.91/%2F?connection_attempts=3&heartbeat_interval=3600'
else if 'BROKER_PORT' in os.environ:
	# RabbitMQ running as docker container
	BROKER_URI = 'amqp://villas:n0rw4y@broker/%2F'