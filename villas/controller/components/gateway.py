from villas.controller.component import Component


class Gateway(Component):

    def __init__(self, manager, **props):
        super().__init__(**props)

        self.set_manager(manager)
