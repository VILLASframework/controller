import kombu
import time
import json
import sys

from villas.controller.command import Command
from villas.controller.commands.simulator import SimulatorCommand


class MonitorCommand(Command):

    @staticmethod
    def add_parser(subparsers):
        parser = subparsers.add_parser('monitor', help='Listen to events')
        parser.set_defaults(func=MonitorCommand.run)

        filt = parser.add_argument_group('Filter simulators')
        filt.add_argument('-r', '--realm')
        filt.add_argument('-c', '--category')
        filt.add_argument('-t', '--type')
        filt.add_argument('-u', '--uuid')

    @staticmethod
    def run(connection, args):
        exchange = kombu.Exchange(name='villas', type='headers')

        headers = SimulatorCommand.get_headers(args)
        headers['x-match'] = 'any' if len(headers) > 0 else 'all'

        queue = kombu.Queue(exchange=exchange,
                            binding_arguments=headers,
                            durable=False)

        consumer = kombu.Consumer(connection,
                                  queues=queue,
                                  on_message=MonitorCommand.on_message)

        try:
            with consumer:
                while True:
                    connection.drain_events()
        except KeyboardInterrupt:
            pass

    @staticmethod
    def on_message(message):
        entry = {
            'time': time.time(),
            'payload': message.payload,
        }

        entry.update(message.properties)

        sys.stdout.write('%s\n' % json.dumps(entry))
        sys.stdout.flush()
