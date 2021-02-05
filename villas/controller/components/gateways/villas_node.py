from villas.controller.components.gateway import Gateway


class VILLASnodeGateway(Gateway):

    def __init__(self, controller, args):
        # Some default properties
        props = {
            'category': 'gateway',
            'type': 'node',
            'sub_type': args['type'],
            'realm': args.get('realm', controller.realm)
        }

        if args['type'] == 'websocket':
            props['ws_url'] = controller.node.api_url + '/' + args['name']

        del args['type']
        props.update(args)

        super().__init__(controller, **props)

    def start(self, message):
        try:
            self.controller.node.request('node.start', {'node': self.name})
            self.controller.reconcile()
        except Exception as e:
            self.logger.warn('Failed to start node: %s', e)

    def stop(self, message):
        try:
            self.controller.node.request('node.stop', {'node': self.name})
            self.controller.reconcile()
        except Exception as e:
            self.logger.warn('Failed to stop node: %s', e)

    def pause(self, message):
        try:
            self.controller.node.request('node.pause', {'node': self.name})
            self.controller.reconcile()
        except Exception as e:
            self.logger.warn('Failed to pause node: %s', e)

    def resume(self, message):
        try:
            self.controller.node.request('node.resume', {'node': self.name})
            self.controller.reconcile()
        except Exception as e:
            self.logger.warn('Failed to resume node: %s', e)

    def reset(self, message):
        try:
            self.controller.node.reset('node.restart', {'node': self.name})
            self.controller.reconcile()
        except Exception as e:
            self.logger.warn('Failed to reset node: %s', e)
