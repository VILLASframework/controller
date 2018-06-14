class SimulationException(Exception):
	def __init__(self, sim, msg, **kwargs):
		super().__init__(sim, msg, kwargs)

		self.msg = msg
		self.info = kwargs
