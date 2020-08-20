from ..component import Component


class Controller(Component):

    def __init__(self, **args):
        super().__init__(**args)

    @staticmethod
    def from_json(json):
        from .controllers import playback, kubernetes

        if json['type'] == 'playback':
            return playback.PlaybackController(**json)
        if json['type'] == 'kubernetes':
            return kubernetes.KubernetesController(**json)
        else:
            return None
