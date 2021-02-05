
import logging

from villas.controller.command import Command
from villas.controller.controller import ControllerMixin

LOGGER = logging.getLogger(__name__)


class DaemonCommand(Command):

    @staticmethod
    def add_parser(subparsers):
        parser = subparsers.add_parser('daemon',
                                       help='Run VILLAScontroller as a daemon')
        parser.set_defaults(func=DaemonCommand.run)

    @staticmethod
    def run(connection, args):
        components = args.config.components

        try:
            d = ControllerMixin(connection, components)
            d.run()
        except KeyboardInterrupt:
            pass
        except ConnectionError:
            LOGGER.error('Failed to connect to broker.')
