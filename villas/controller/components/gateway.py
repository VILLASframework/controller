from villas.controller.component import Component


class Gateway(Component):

    def __init__(self, manager, **props):
        self.manager = manager

        super().__init__(**props)
