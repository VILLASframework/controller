# SPDX-FileCopyrightText: 2014-2025 The VILLASframework Authors
# SPDX-License-Identifier: Apache-2.0

from villas.controller.components.gateway import Gateway


class VILLASrelayGateway(Gateway):

    def __init__(self, manager, args):
        # Some default properties
        props = {
            'category': 'gateway',
            'type': 'villas-relay',
            'realm': manager.realm,
            'name': args['identifier']
        }

        props['ws_url'] = manager.api_url_external + '/' + args['identifier']

        props.update(args)

        super().__init__(manager, **props)
