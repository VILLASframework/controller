from .. import command

import villas.controller.controller

class DaemonCommand(command.Command):

	@staticmethod
	def add_parser(subparsers):
		parser = subparsers.add_parser('daemon', help = 'Run VILLAScontroller as a daemon')
		parser.set_defaults(func = DaemonCommand.run)

	@staticmethod
	def run(connection, args):
		d = villas.controller.controller.Controller(connection, args.config.simulators)

		try:
			d.run()
		except KeyboardInterrupt:
			pass
