import argparse

class Command(object):

	@staticmethod
	def add_parser(subparsers):
		pass

	@staticmethod
	def register_subcommands(parser):
		subparsers = parser.add_subparsers(title = 'subcommands', metavar = 'SUBCOMMAND', help = 'Available subcommands:')
		subparsers.required = True
		subparsers.dest = 'command'

		from . import commands

		for subcommand in Command.__subclasses__():
			subcommand.add_parser(subparsers)
