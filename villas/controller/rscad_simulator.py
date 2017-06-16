import socket
import time

from simulator import Simulator

from rtds.rack.rack import Rack

class RscadSimulator(Simulator, Rack):

	def __init__(self, host, number):
		Rack.__init__(self, host, number)
		
	def start(self, body):
		Simulator.start(self, body)
		
	def stop(self, body):
		Simulator.stop(self, body)

	def pause(self, body):
		Simulator.pause(self, body)

	def resume(self, body):
		Simulator.resume(self, body)

	def get_state(self):
		try:
			user, case = self.ping()
			
			if len(user) > 0:
				state = {
					'status' : 'running',
					'user' : user,
					'case' : case
				}
			else:
				state = {
					'status' : 'free'
				}
		except socket.timeout:
			state = {
				'status' : 'offline'
			}
			
		state['time'] = int(round(time.time() * 1000))

		return state