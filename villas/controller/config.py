import yaml
import argparse
import logging
import os
import dotmap
import uuid
from typing import List

from os import getcwd
from xdg import (
    xdg_config_dirs,
    xdg_config_home,
)

from villas.controller.component import Component
from villas.controller.util import merge

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

    DEFAULT_CONFIG = {
        'broker': {
            'url': 'amqp://localhost:5672/%2F'
        },
        'api': {
            'enabled': True,
            'port': 8089
        },
        'components': [],
        # 'workdir': '/var/villas/controller/simulators/'
        'workdir': os.getcwd(),
        'uuid': str(uuid.uuid4())
    }

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
                    self.load(fp)
            else:
                self.config = {}  # Start without config
        else:
            self.load(fp)

    def load(self, fp):
        config = yaml.load(fp, Loader=yaml.FullLoader)
        merged = merge(self.DEFAULT_CONFIG, config)

        self.config = dotmap.DotMap(merged)

    def find_default_path(self, filename='config',
                          suffixes=['json', 'yaml', 'yml']):
        for path in Config.DEFAULT_PATHS:
            for suffix in suffixes:
                fn = os.path.join(path, f'{filename}.{suffix}')
            if os.access(fn, os.R_OK):
                return fn

    @property
    def components(self) -> List[Component]:
        return [Component.from_dict(c) for c in self.config.components]

    def __getattr__(self, attr):
        return self.config.get(attr)

    def check(self):
        uuids = [c.uuid for c in self.components]

        dups_uuids = set([u for u in uuids if uuids.count(u) > 1])

        if len(dups_uuids) > 0:
            raise RuntimeError('Duplicate UUIDs: ' + dups_uuids)
