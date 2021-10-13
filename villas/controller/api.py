import threading
import logging
import asyncio
from tornado.ioloop import IOLoop
import tornado.web

LOGGER = logging.getLogger(__name__)
REGEX_UUID = r'\b[0-9a-fA-F]{8}\b-[0-9a-fA-F]{4}-[0-9a-fA-F]' \
             r'{4}-[0-9a-fA-F]{4}-\b[0-9a-fA-F]{12}\b'


class RequestHandler(tornado.web.RequestHandler):

    def initialize(self, controller):
        self.controller = controller


class Api(threading.Thread):

    def __init__(self, controller):
        super().__init__()

        self.controller = controller

    def run(self):
        self.app = tornado.web.Application(self.handlers)

        # Create new event loop for this thread
        aio_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(aio_loop)

        port = self.controller.config.api.port
        self.app.listen(port)

        LOGGER.info('Starting API')

        self.loop = IOLoop.current(instance=True)
        self.loop.start()

    @property
    def handlers(self):
        from villas.controller.handlers.component import ComponentRequestHandler  # noqa E501
        from villas.controller.handlers.main import MainRequestHandler
        from villas.controller.handlers.health import HealthRequestHandler

        args = {
            'controller': self.controller
        }

        return [
            (r'/', MainRequestHandler, args),
            (r'/health', HealthRequestHandler, args),
            (r'/component/('+REGEX_UUID+r')', ComponentRequestHandler, args)
        ]
