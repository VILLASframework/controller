from ..controller import Controller


class PlaybackController(Controller):

    def __init__(self, **args):
        super().__init__(**args)

        self.controller_state = 'm1'

        self.m1_uuid = 'edaf647a-f012-11e8-b711-320084a2b301'
        self.m2_uuid = '73469f62-f1ae-11e8-9f9a-375372c8e719'

        self._state = 'running'

    def on_message(self, message):
        self.logger.debug('Received message: %s', message.payload)

        if 'action' in message.payload:
            if message.payload['action'] == 'toggle':
                self.toggle()

    def toggle(self):
        if self.controller_state == 'm1':
            self.controller_state = 'm2'

            self.producer.publish(
                {
                    'action': 'pause'
                },
                headers={
                    'uuid': self.m2_uuid
                }
            )

            self.producer.publish(
                {
                    'action': 'resume'
                },
                headers={
                    'uuid': self.m1_uuid
                }
            )

        elif self.controller_state == 'm2':
            self.controller_state = 'm1'

            self.producer.publish(
                {
                    'action': 'pause'
                },
                headers={
                    'uuid': self.m1_uuid
                }
            )

            self.producer.publish(
                {
                    'action': 'resume'
                },
                headers={
                    'uuid': self.m2_uuid
                }
            )
