
import logging
import functools as ft
import villas.controller.controller
from villas.controller.components.gateways.villas_node import VILLASnodeGateway
from villas.controller.command import Command

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

        # Automatically create a VILLASnode Gateway if not present in config
        node_present = ft.reduce(lambda present, comp: present or type(comp)
                                 is VILLASnodeGateway, components, False)
        if not node_present and not args.config.json.get('skip_node'):
            LOGGER.info('Creating default VILLASnodeGateway component')
            node_comp = VILLASnodeGateway()

            components.append(node_comp)

        try:
            d = villas.controller.controller.Controller(connection, components)
            d.run()
        except KeyboardInterrupt:
            pass
        except ConnectionError:
            LOGGER.error('Failed to connect to broker.')
