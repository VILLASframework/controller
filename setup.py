from setuptools import setup
from glob import glob

setup(
    data_files=[
        ('/etc/villas/controller', glob('etc/*.{json,yaml}')),
        ('/etc/systemd/system', ['villas-controller.service'])
    ]
)
