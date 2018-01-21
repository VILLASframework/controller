from setuptools import setup, find_packages

setup(
	name="villas-controller",
	version="0.1.0",
	description="A controller/orchestration API for real-time power system simulators",
	url="http://git.rwth-aachen.de/acs/public/villas/VILLAScontroller",
	author="Steffen Vogel",
	author_email="stvogel@eonrc.rwth-aachen.de",
	classifiers=[  # Optional
		'Development Status :: 3 - Alpha',
		'License :: OSI Approved :: GPL3',
		'Programming Language :: Python :: 3'
	],
	packages=find_packages(),
	install_requires=[
		'kombu'
	],
	scripts=[
		'bin/villas-ctl'
	]
)
