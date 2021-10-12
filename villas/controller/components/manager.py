from villas.controller.component import Component


class Manager(Component):

    def __init__(self, **args):
        super().__init__(**args)

        # Dict (uuid -> component) of components
        # which are managed by this controller
        self.components = {}

    @property
    def status(self):
        return {
            'components': [c for c in self.components],
            **super().status
        }

    @staticmethod
    def from_dict(dict):
        type = dict.get('type', 'generic')

        if type == 'generic':
            from villas.controller.components.managers import generic
            return generic.GenericManager(**dict)
        if type == 'kubernetes':
            from villas.controller.components.managers import kubernetes
            return kubernetes.KubernetesManager(**dict)
        if type == 'kubernetes-simple':
            from villas.controller.components.managers import kubernetes_simple
            return kubernetes_simple.KubernetesManagerSimple(**dict)
        if type == 'villas-node':
            from villas.controller.components.managers import villas_node  # noqa E501
            return villas_node.VILLASnodeManager(**dict)
        if type == 'villas-relay':
            from villas.controller.components.managers import villas_relay  # noqa E501
            return villas_relay.VILLASrelayManager(**dict)
        else:
            raise Exception(f'Unknown type: {type}')

    def add_component(self, comp):
        print(self.name)
        print(comp)
        if comp.uuid in self.mixin.components:
            # raise KeyError
            self.logger.error('UUID %s already exists, not added', comp.uuid)
            return

        comp.set_manager(self)

        self.components[comp.uuid] = comp
        self.mixin.components[comp.uuid] = comp

        self.logger.info('Added new component %s', comp)

    def remove_component(self, comp):
        comp.change_state('gone')

        del self.components[comp.uuid]
        del self.mixin.components[comp.uuid]

        self.logger.info('Removed component %s', comp)

    def run_action(self, action, payload):
        if action == 'create':
            #print(message.payload)
            #self.create(message)
            self.create(payload)
        elif action == 'delete':
            self.delete(payload)
        else:
            super().run_action(action, payload)

    def create(self, payload):
        raise NotImplementedError()

    def delete(self, payload):
        raise NotImplementedError()

    def on_shutdown(self):
        super().on_shutdown()

        # Once the villas controller process is terminated,
        # the managers are effectively shutdown and cant act on any
        # create/delete actions, therefore we let them
        # change their state to 'shutdown'.
        self.change_state('shutdown')
