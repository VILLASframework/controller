import json
import argparse
import logging
import os

from os import getcwd
from xdg import (
    xdg_config_dirs,
    xdg_config_home,
 )

from villas.controller.component import Component

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

    DEFAULT_PATHS = xdg_config_dirs() + [
                    xdg_config_home(),
                    getcwd(),
                    os.path.join(getcwd(), 'etc'),
                    '/etc/villas/controller/' ]

    def __init__(self, fp=None):
        if fp is None:
            fn = self.find_default_path()
            if fn:
                with open(fn) as fp:
                    self.json = json.load(fp)

        else:
            self.json = json.load(fp)

    def find_default_path(self, filename='config.json'):
        for path in Config.DEFAULT_PATHS:
            fn = os.path.join(path, filename)
            if os.access(fn, os.R_OK):
                return fn

    @property
    def components(self):
        return [Component.from_json(js) for js in self.json['components']]
