import logging
import argparse
import kombu
import socket
import sys
import os.path
import datetime
import termcolor

from villas.controller import __version__ as version

from villas.controller.config import Config, ConfigType
from villas.controller.command import Command

LOGGER = logging.getLogger('villas.controller')

_LOG_LEVEL_STRINGS = ['CRITICAL', 'ERROR', 'WARNING', 'INFO', 'DEBUG']


def _log_level_string_to_int(log_level_string):
    if log_level_string not in _LOG_LEVEL_STRINGS:
        message = 'invalid choice: {0} (choose from {1})'.format(
            log_level_string, _LOG_LEVEL_STRINGS)
        raise argparse.ArgumentTypeError(message)

    log_level_int = getattr(logging, log_level_string, logging.INFO)

    # check the logging log_level_choices have
    # not changed from our expected values
    assert isinstance(log_level_int, int)

    return log_level_int


def setup_logging(args):
    logging.basicConfig(level=args.log_level,
                        stream=sys.stderr,
                        format='%(asctime)s | %(levelname)s |'
                               ' %(name)s | %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S')

    root = logging.getLogger(__name__)
    root.setLevel(args.log_level)

    amqp = logging.getLogger('amqp')
    amqp.setLevel(logging.INFO)

    kombu = logging.getLogger('kombu')
    kombu.setLevel(args.log_level)

    villas = logging.getLogger('villas')
    villas.setLevel(args.log_level)


def setup_argparse():
    # Main parser
    ver = termcolor.colored(version, 'blue')
    year = datetime.date.today().year

    parser = argparse.ArgumentParser(
        prog=os.path.basename(sys.argv[0]),
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(f'VILLAScontroller {ver}\n'
                f' Copyright 2014-{year}, Institute for Automation '
                'of Complex Power Systems, EONERC\n'
                ' Steffen Vogel <svogel2@eonerc.rwth-aachen.de>\n')
    )

    parser.add_argument('-b', '--broker',
                        help='URL of AMQP broker')

    parser.add_argument('-v', '--version',
                        help='Show program version and exit',
                        action='version',
                        version=version)

    parser.add_argument('-c', '--config',
                        help='Path of configuration file',
                        type=ConfigType(),
                        default=Config())

    parser.add_argument('-d', '--log-level',
                        default='INFO',
                        dest='log_level',
                        type=_log_level_string_to_int,
                        nargs='?',
                        help='Set the logging output level.'
                             f' {_LOG_LEVEL_STRINGS}')

    # Add parsers for subcommands
    Command.register_subcommands(parser)

    return parser


def main():
    # Show log messages during parsing
    logger = logging.getLogger('villas')
    logger.setLevel(logging.DEBUG)

    parser = setup_argparse()
    args = parser.parse_args()

    setup_logging(args)

    try:
        broker_url = args.broker or args.config.broker.url
    except AttributeError:
        LOGGER.error('A broker URL must be provided either via a command line '
                     'parameter or a configuration file')
        return -1
    try:
        with kombu.Connection(broker_url, connect_timeout=3) as c:
            LOGGER.info(f'Connecting to: {broker_url}')
            c.connect()

            args.func(c, args)

            c.release()

    except ConnectionRefusedError:
        LOGGER.error('Connection refused!')
    except socket.timeout:
        LOGGER.error('Connection timeout!')
    else:
        LOGGER.info('Goodbye')
