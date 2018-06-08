import json
import argparse
import logging
import os

from . import simulator

LOGGER = logging.getLogger(__name__)

class ConfigType(argparse.FileType):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def __call__(self, arg):
		f = super().__call__(arg)
		return Config(f)

class Config(object):

	DEFAULT_PATHS = [ 'config.json', 'etc/config.json', '/etc/villas/controller/config.json' ]

	def __init__(self, f = None):
		if f is None:
			f = self.find_default_path()

		LOGGER.info('Reading configuration from %s' % f)

		with open(f) as fp:
			self.json = json.load(fp)

	def find_default_path(self):
		for path in Config.DEFAULT_PATHS:
			if os.access(path, os.R_OK):
				return path

	@property
	def simulators(self):
		return [ simulator.Simulator.from_json(js) for js in self.json['simulators'] ]
