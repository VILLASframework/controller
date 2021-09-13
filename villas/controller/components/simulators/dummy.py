import threading

from villas.controller.components.simulator import Simulator


class DummySimulator(Simulator):

    start_schema = {
        '$schema': 'http://json-schema.org/draft-07/schema',
        'type': 'object',
        'default': {},
        'required': [
            'runtime'
        ],
        'properties': {
            'runtime': {
                '$id': '#/properties/runtime',
                'description': 'The run time of the simulation',
                'type': 'number',
                'default': 1.0,
                'examples': [
                    3.0
                ]
            }
        }
    }

    def __init__(self, **args):
        super().__init__(**args)

        self.timer = None

    def __del__(self):
        if self.timer:
            self.timer.cancel()

    def _schedule_state_transition(self, state, time=1.0):
        self.timer = threading.Timer(time, self.change_state, args=[state])
        self.timer.start()

    def start(self, message):
        super().start(message)

        runtime = self.params.get('runtime', 1.0)

        self._schedule_state_transition('running', runtime)

    def stop(self, message):
        super().stop(message)

        self._schedule_state_transition('idle')

    def pause(self, message):
        super().pause(message)

        self._schedule_state_transition('paused')

    def resume(self, message):
        super().resume(message)

        self._schedule_state_transition('running')

    def shutdown(self, message):
        super().shutdown(message)

        self._schedule_state_transition('shutdown')

    def reset(self, message):
        super().reset(message)

        self._schedule_state_transition('idle')
