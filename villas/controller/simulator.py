
class Simulator:

	def __init__(self):
		self.state = { 'state' : 'unknown' }
	
	def start(self, body):
		print 'Starting simulation: ', body
		
	def stop(self, body):
		print 'Stop simulation: ', body

	def pause(self, body):
		print 'Pause simulation: ', body

	def resume(self, body):
		print 'Resume simulation: ', body
