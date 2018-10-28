from setuptools import setup
from pkg_resources import parse_version  # part of `setuptools`
from glob import glob
import subprocess
import re
import os

def cleanhtml(raw_html):
	cleanr = re.compile('<.*?>')
	cleantext = re.sub(cleanr, '', raw_html)
	return cleantext

def read(fname):
	dname = os.path.dirname(__file__)
	fname = os.path.join(dname, fname)

	with open(fname) as f:
		contents = f.read()
		sanatized = cleanhtml(contents)

	try:
		from m2r import M2R
		m2r = M2R()
		return m2r(sanatized)
	except:
		return sanatized

setup(
	name = 'villas-controller',
	version = '0.3.0',
	description = 'A controller/orchestration API for real-time power system simulators',
	long_description = read('README.md'),
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
		'pycurl'
	],
	data_files = [
		('/etc/villas/controller', glob('etc/*.json')),
		('/etc/systemd/system', ['villas-controller.service'])
	],
	scripts = glob('bin/*')
)
