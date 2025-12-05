# SPDX-FileCopyrightText: 2014-2025 The VILLASframework Authors
# SPDX-License-Identifier: Apache-2.0

from setuptools import setup
from glob import glob

setup(
    data_files=[
        ('/etc/villas/controller', glob('etc/*.{json,yaml}')),
        ('/etc/systemd/system', ['villas-controller.service'])
    ]
)
