from setuptools import setup, find_namespace_packages
from glob import glob

import os
import re

def get_version():
    here = os.path.abspath(os.path.dirname(__file__))
    init_file = os.path.join(here, "villas", "controller", "__init__.py")

    with open(init_file, "r") as f:
        content = f.read()

    match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", content, re.M)
    if match:
        return match.group(1)

    raise RuntimeError("Version not found")

setup(
    name='villas-controller',
    version=get_version(),
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
        'License :: OSI Approved :: Apache Software License',
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
