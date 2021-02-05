from villas.controller.component import Component
from villas.controller.controllers import playback, kubernetes, villas_node, villas_relay


class Controller(Component):

    def __init__(self, **args):
        super().__init__(**args)

    @staticmethod
    def from_json(json):
        if json['type'] == 'kubernetes':
            return kubernetes.KubernetesController(**json)
        if json['type'] == 'villas-node':
            return villas_node.VILLASnodeController(**json)
        if json['type'] == 'villas-relay':
            return villas_relay.VILLASrelayController(**json)
        else:
            return None
