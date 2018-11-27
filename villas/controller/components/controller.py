import logging

from ..component import Component

class Controller(Component):

	def __init__(self, **args):
		super().__init__(**args)

	@staticmethod
	def from_json(json):
		from .controllers import playback

		if json['type'] == 'playback':
			return playback.PlaybackController(**json)
		else:
			return None
