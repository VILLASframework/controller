from villas.controller.component import Component


class Controller(Component):

    def __init__(self, **args):
        super().__init__(**args)

        # Dict (uuid -> component) of components
        # which are managed by this controller
        self.components = {}

    @staticmethod
    def from_json(json):

        if 'type' in json:
            type = json.get('type')

            if type == 'kubernetes':
                from villas.controller.components.controllers import kubernetes
                return kubernetes.KubernetesController(**json)
            if type == 'villas-node':
                from villas.controller.components.controllers import villas_node  # noqa E501
                return villas_node.VILLASnodeController(**json)
            if type == 'villas-relay':
                from villas.controller.components.controllers import villas_relay  # noqa E501
                return villas_relay.VILLASrelayController(**json)
            else:
                raise Exception(f'Unknown type: {type}')

        else:
            return Controller(**json)

    def add_component(self, comp):
        if comp.uuid in self.mixin.components:
            raise KeyError

        self.components[comp.uuid] = comp
        self.mixin.components[comp.uuid] = comp

        self.logger.info('Controller %s added new component %s', self, comp)

    def remove_component(self, comp):
        del self.components[comp.uuid]
        del self.mixin.components[comp.uuid]

        self.logger.info('Controller %s removed component %s', self, comp)

    def run_action(self, action, message):
        if action == 'create':
            self.create(message)
        elif action == 'delete':
            self.delete(message)
        else:
            super().run_action(action, message)

    def create(self, message):
        comp = Component.from_json(message.payload.get('parameters'))

        try:
            self.add_component(comp)
        except KeyError:
            self.logger.error('A component with the UUID %s already exists',
                              comp.uuid)

    def delete(self, message):
        params = message.payload.get('parameters')
        uuid = params.get('uuid')

        try:
            comp = self.components[uuid]

            self.remove_component(comp)

        except KeyError:
            self.logger.error('There is not component with UUID: %s', uuid)
