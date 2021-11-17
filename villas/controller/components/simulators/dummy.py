import threading

from villas.controller.components.simulator import Simulator


class DummySimulator(Simulator):

    def __init__(self, **args):
        super().__init__(**args)

        self.timer = None

    def __del__(self):
        if self.timer:
            self.timer.cancel()

    def _schedule_state_transition(self, state, time=1.0):
        self.timer = threading.Timer(time, self.change_state, args=[state])
        self.timer.start()

    def start(self, payload):
        super().start(payload)

        runtime = self.params.get('runtime', 1.0)

        self._schedule_state_transition('running', runtime)

    def stop(self, payload):
        super().stop(payload)

        self._schedule_state_transition('idle')

    def pause(self, payload):
        super().pause(payload)

        self._schedule_state_transition('paused')

    def resume(self, payload):
        super().resume(payload)

        self._schedule_state_transition('running')

    def shutdown(self, payload):
        super().shutdown(payload)

        self._schedule_state_transition('shutdown')

    def reset(self, payload):
        super().reset(payload)

        self._schedule_state_transition('idle')
