from villas.controller.component import Component


class Gateway(Component):

    def __init__(self, controller, **props):
        self.controller = controller

        super().__init__(**props)
