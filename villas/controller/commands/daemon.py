from .. import command

import logging
import villas.controller.controller

LOGGER = logging.getLogger(__name__)

class DaemonCommand(command.Command):

	@staticmethod
	def add_parser(subparsers):
		parser = subparsers.add_parser('daemon', help = 'Run VILLAScontroller as a daemon')
		parser.set_defaults(func = DaemonCommand.run)

	@staticmethod
	def run(connection, args):
		try:
			d = villas.controller.controller.Controller(connection, args.config.simulators)
			d.run()
		except KeyboardInterrupt:
			pass
		except ConnectionError:
			LOGGER.error("Failed to connect to broker.")
