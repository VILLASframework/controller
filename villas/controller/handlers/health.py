from villas.controller.api import RequestHandler


class HealthRequestHandler(RequestHandler):

    def get(self):
        self.write({
            'status': 'ok'
        })
