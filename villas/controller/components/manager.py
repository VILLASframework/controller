from villas.controller.component import Component


class Manager(Component):

    def __init__(self, **args):
        super().__init__(**args)

        # Dict (uuid -> component) of components
        # which are managed by this controller
        self.components = {}

    @staticmethod
    def from_dict(dict):
        type = dict.get('type', 'generic')

        if type == 'generic':
            dict['type'] = 'generic'
            return Manager(**dict)
        if type == 'kubernetes':
            from villas.controller.components.managers import kubernetes
            return kubernetes.KubernetesController(**dict)
        if type == 'villas-node':
            from villas.controller.components.managers import villas_node  # noqa E501
            return villas_node.VILLASnodeController(**dict)
        if type == 'villas-relay':
            from villas.controller.components.managers import villas_relay  # noqa E501
            return villas_relay.VILLASrelayController(**dict)
        else:
            raise Exception(f'Unknown type: {type}')

    def add_component(self, comp):
        if comp.uuid in self.mixin.components:
            raise KeyError

        self.components[comp.uuid] = comp
        self.mixin.components[comp.uuid] = comp

        self.logger.info('Added new component %s', comp)

    def remove_component(self, comp):
        del self.components[comp.uuid]
        del self.mixin.components[comp.uuid]

        self.logger.info('Removed component %s', comp)

    def run_action(self, action, message):
        if action == 'create':
            self.create(message)
        elif action == 'delete':
            self.delete(message)
        else:
            super().run_action(action, message)

    def create(self, message):
        comp = Component.from_dict(message.payload.get('parameters'))

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
