import threading

from .. import simulator


class DummySimulator(simulator.Simulator):

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
        self._schedule_state_transition('running')

    def stop(self, message):
        self._schedule_state_transition('idle')

    def pause(self, message):
        self._schedule_state_transition('paused')

    def resume(self, message):
        self._schedule_state_transition('running')

    def shutdown(self, message):
        self._schedule_state_transition('shutdown')

    def reset(self, message):
        self._schedule_state_transition('idle')

        super().reset(message)
