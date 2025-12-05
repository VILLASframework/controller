# SPDX-FileCopyrightText: 2014-2025 The VILLASframework Authors
# SPDX-License-Identifier: Apache-2.0

from villas.controller.api import RequestHandler


class MainRequestHandler(RequestHandler):

    def get(self):
        self.write({
            'components': list(self.controller.components.keys()),
            'status': {
                **self.controller.status
            }
        })
