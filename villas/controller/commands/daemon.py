# SPDX-FileCopyrightText: 2014-2025 The VILLASframework Authors
# SPDX-License-Identifier: Apache-2.0

import logging

from villas.controller.command import Command
from villas.controller.controller import ControllerMixin

LOGGER = logging.getLogger(__name__)


class DaemonCommand(Command):

    @staticmethod
    def add_parser(subparsers):
        parser = subparsers.add_parser('daemon',
                                       help='Run VILLAScontroller as a daemon')
        parser.set_defaults(func=DaemonCommand.start)

    @staticmethod
    def start(connection, args):

        try:
            d = ControllerMixin(connection, args)
            d.start()
        except KeyboardInterrupt:
            d.shutdown()
        except ConnectionError:
            LOGGER.error('Failed to connect to broker.')
