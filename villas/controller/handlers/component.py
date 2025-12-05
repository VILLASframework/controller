# SPDX-FileCopyrightText: 2014-2025 The VILLASframework Authors
# SPDX-License-Identifier: Apache-2.0

import json
from tornado.web import HTTPError
from http import HTTPStatus
from functools import wraps


from villas.controller.api import RequestHandler
from villas.controller.exceptions import SimulationException


def with_component(f):

    @wraps(f)
    def wrapper(self, uuid):
        try:
            component = self.controller.components[uuid]

            f(self, component)
        except KeyError:
            raise HTTPError(HTTPStatus.NOT_FOUND)

    return wrapper


class ComponentRequestHandler(RequestHandler):

    @with_component
    def get(self, component):
        self.write(component.status)

    @with_component
    def post(self, component):
        payload = json.loads(self.request.body)

        action = payload.get('action')
        if action is None:
            raise HTTPError(HTTPStatus.BAD_REQUEST)

        try:
            component.run_action(action, payload)
            self.write(component.status)

        except SimulationException as se:
            self.write({
                'exception': {
                    'msg': se.msg,
                    'args': se.args
                },
                **component.status
            })
            self.send_error(HTTPStatus.BAD_REQUEST)
