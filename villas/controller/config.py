import yaml
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


class Config:

    DEFAULT_PATHS = xdg_config_dirs() + [
                    xdg_config_home(),
                    getcwd(),
                    os.path.join(getcwd(), 'etc'),
                    '/etc/villas/controller/']

    def __init__(self, fp=None):
        if fp is None:
            fn = self.find_default_path()
            if fn:
                with open(fn) as fp:
                    self.dict = yaml.load(fp, Loader=yaml.FullLoader)
            else:
                pass  # Start without config
        else:
            self.dict = yaml.load(fp, Loader=yaml.FullLoader)

    def find_default_path(self, filename='config',
                          suffixes=['json', 'yaml', 'yml']):
        for path in Config.DEFAULT_PATHS:
            for suffix in suffixes:
                fn = os.path.join(path, f'{filename}.{suffix}')
            if os.access(fn, os.R_OK):
                return fn

    @property
    def components(self):
        return [Component.from_dict(c) for c in self.dict['components']]

    def check(self):
        uuids = [c.uuid for c in self.components]

        dups_uuids = set([u for u in uuids if uuids.count(u) > 1])

        if len(dups_uuids) > 0:
            raise RuntimeError('Duplicate UUIDs: ' + dups_uuids)
