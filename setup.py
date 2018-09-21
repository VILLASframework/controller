from setuptools import setup, find_packages
from pkg_resources import parse_version  # part of `setuptools`
from glob import glob
import subprocess
import re
import os

def git_version():
	"""Return version with local version identifier."""

	try:
		import git

		repo = git.Repo('.git')
		repo.git.status()

		latest_tag = repo.git.describe(match='v[0-9]*', tags=True, abbrev=0)
		sha = repo.head.commit.hexsha[:6]

		version = latest_tag.lstrip('v')

		return '{v}-{sha}'.format(v = version, sha = sha)
	except:
		return 'unknown'

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
	version = git_version(),
	description = 'A controller/orchestration API for real-time power system simulators',
	long_description = read('README.md'),
	url = 'https://www.fein-aachen.org/projects/villas-controller/',
	author = 'Steffen Vogel',
	author_email = 'stvogel@eonrc.rwth-aachen.de',
	maintainer = 'Steffen Vogel',
	maintainer_email = 'stvogel@eonerc.rwth-aachen.de',
	license = 'GPL-3.0',
	keywords = 'simulation controller villas',
	classifiers = [  # Optional
		'Development Status :: 3 - Alpha',
		'License :: OSI Approved :: GPL3',
		'Programming Language :: Python :: 3'
	],
	packages = find_packages(),
	setup_requires = [
        	'm2r',
		'gitpython'
	],
	install_requires = [
		'kombu',
		'termcolor',
		'psutils'
	],
	data_files = [
		('/etc/villas/controller', glob('etc/*.json')),
		('/etc/systemd/system', ['villas-controller.service'])
	],
	scripts = glob('bin/*')
)
