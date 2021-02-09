from villas.controller.components.gateway import Gateway


class VILLASrelayGateway(Gateway):

    def __init__(self, controller, args):
        # Some default properties
        props = {
            'category': 'gateway',
            'type': 'relay',
            'realm': controller.realm,
            'name': args['identifier']
        }

        props['ws_url'] = controller.ws_url + '/' + args['identifier']

        props.update(args)

        super().__init__(controller, **props)
