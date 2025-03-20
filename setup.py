from setuptools import setup, find_namespace_packages
from glob import glob

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

try:
    from villas.controller import __version__ as version
except ModuleNotFoundError:
    version = "0.0.0"

with open('README.md') as f:
    long_description = f.read()

setup(
    name='villas-controller',
    version=version,
    description='A controller/orchestration API for real-time '
                'power system simulators',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://www.fein-aachen.org/projects/villas-controller/',
    author='Steffen Vogel',
    author_email='acs-software@eonerc.rwth-aachen.de',
    license='Apache License 2.0',
    keywords='simulation controller villas',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: Apache Software License'
        'Programming Language :: Python :: 3'
    ],
    packages=find_namespace_packages(include=['villas.*']),
    install_requires=[
        'dotmap',
        'kombu',
        'termcolor',
        'psutil',
        'requests',
        'villas-node>=0.10.2',
        'kubernetes',
        'xdg',
        'PyYAML',
        'tornado',
        'jsonschema>=4.1.0',
        'psutil',
        'pyusb'
    ],
    data_files=[
        ('/etc/villas/controller', glob('etc/*.{json,yaml}')),
        ('/etc/systemd/system', ['villas-controller.service'])
    ],
    entry_points={
        'console_scripts': [
            'villas-ctl=villas.controller.main:main',
            'villas-controller=villas.controller.main:main'
        ],
    },
    include_package_data=True
)
