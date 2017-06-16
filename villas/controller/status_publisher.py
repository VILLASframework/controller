
class StatusPublisher(amqp.Publisher):
	def __init__(self, channel, simulator):
		amqp.Publisher(self, channel)
		
		self._simulator = simulator
		
		self.

	def configure(self):
		self._exchange = self._channel.exchange_declare(
			exchange='status'
			type='topic'
		)
		
		print "Configure from StatusPubsliher"

	def send(self):
		state = self._simulator.get_state()
	
		self._channel.basic_publish(
			exchange = 'status',
			routing_key = 'status.simulator.rtds.rack1',
			body = json.dumps(state),
			properties = pika.BasicProperties(content_type='application/json')
		)