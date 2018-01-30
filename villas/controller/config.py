import json
import argparse
import logging

from . import simulator

LOGGER = logging.getLogger(__name__)

class ConfigType(argparse.FileType):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def __call__(self, arg):
		f = super().__call__(arg)
		return Config(f)

class Config(object):

	DEFAULT_PATHS = [ '/etc/villas/controller.json', '~/.villas/controller.json', 'config.json' ]

	def __init__(self, f = None):
		if f:
			self.json = json.load(f)
		else:
			self.try_default_paths()

	def try_default_paths(self):
		for path in Config.DEFAULT_PATHS:
			try:
				with open(path) as f:
					self.json = json.load(f)
			except IOError:
				pass

	@property
	def simulators(self):
		return [ simulator.Simulator.from_json(js) for js in self.json['simulators'] ]
