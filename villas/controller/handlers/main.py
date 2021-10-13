from villas.controller.api import RequestHandler


class MainRequestHandler(RequestHandler):

    def get(self):
        self.write({
            'components': list(self.controller.components.keys()),
            'status': {
                **self.controller.status
            }
        })
