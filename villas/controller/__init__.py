import pkg_resources  # part of setuptools

__version__ = pkg_resources.require('villas-controller')[0].version
