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
            from villas.controller.components.managers import generic
            return generic.GenericManager(**dict)
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

        comp.set_manager(self)

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
        raise NotImplementedError()

    def delete(self, message):
        raise NotImplementedError()
