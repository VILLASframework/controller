from setuptools import setup
from glob import glob

with open('README.md') as f:
    long_description = f.read()

setup(
	name = 'villas-controller',
	version = '0.3.0',
	description = 'A controller/orchestration API for real-time power system simulators',
	long_description = long_description,
	long_description_content_type = 'text/markdown',
	url = 'https://www.fein-aachen.org/projects/villas-controller/',
	author = 'Steffen Vogel',
	author_email = 'acs-software@eonerc.rwth-aachen.de',
	license = 'GPL-3.0',
	keywords = 'simulation controller villas',
	classifiers = [
		'Development Status :: 3 - Alpha',
		'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
		'Programming Language :: Python :: 3'
	],
	packages = [ 'villas.controller' ],
	setup_requires = [
		'm2r',
		'gitpython'
	],
	install_requires = [
		'kombu',
		'termcolor',
		'psutil',
		'pycurl',
		'villas-node'
	],
	data_files = [
		('/etc/villas/controller', glob('etc/*.json')),
		('/etc/systemd/system', ['villas-controller.service'])
	],
	scripts = glob('bin/*')
)
