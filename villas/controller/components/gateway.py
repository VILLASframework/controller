import logging

from ..component import Component

class Gateway(Component):

	def __init__(self, **args):
		super().__init__(**args)

	@staticmethod
	def from_json(json):
		from .gateways import villas_node

		if json['type'] == 'villas-node':
			return villas_node.VILLASnodeGateway(**json)
		else:
			return None
