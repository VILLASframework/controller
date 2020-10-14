from villas.controller.component import Component


class Gateway(Component):

    def __init__(self, **args):
        super().__init__(**args)

    @staticmethod
    def from_json(json):
        return None
