import json
import argparse
import logging
import os

from .component import Component

LOGGER = logging.getLogger(__name__)


class ConfigType(argparse.FileType):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __call__(self, arg):
        if arg is None:
            return Config()
        else:
            f = super().__call__(arg)
            return Config(f)


class Config(object):

    DEFAULT_PATHS = ['config.json',
                     'etc/config.json',
                     '/etc/villas/controller/config.json']

    def __init__(self, fp=None):
        if fp is None:
            f = self.find_default_path()
            if f:
                fp = open(f)

        if fp is None:
            raise RuntimeError('Failed to load configuration')

        self.json = json.load(fp)

    def find_default_path(self):
        for path in Config.DEFAULT_PATHS:
            if os.access(path, os.R_OK):
                return path

    @property
    def components(self):
        return [Component.from_json(js) for js in self.json['components']]
