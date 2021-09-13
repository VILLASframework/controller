from villas.controller.components.manager import Manager
from villas.controller.component import Component


class GenericManager(Manager):

    create_schema = {
        '$schema': 'http://json-schema.org/draft-07/schema',
        '$id': 'http://example.com/example.json',
        'type': 'object',
        'default': {},
        'required': [
            'name',
            'category',
            'location',
            'owner',
            'realm',
            'type',
            'api_url',
            'ws_url'
        ],
        'properties': {
            'name': {
                '$id': '#/properties/name',
                'type': 'string',
                'title': 'Component name',
                'default': 'New Component',
                'examples': [
                    'Generic Simulator #1'
                ]
            },
            'owner': {
                '$id': '#/properties/owner',
                'type': 'string',
                'title': 'Component owner',
                'default': '',
                'examples': [
                    'rmr',
                    'svg'
                ]
            },
            'realm': {
                '$id': '#/properties/realm',
                'type': 'string',
                'title': 'Component realm',
                'default': '',
                'examples': [
                    'de.rwth-aachen.eonerc.acs'
                ]
            },
            'category': {
                '$id': '#/properties/category',
                'type': 'string',
                'title': 'Component category',
                'default': '',
                'examples': [
                    'simulator'
                ]
            },
            'location': {
                '$id': '#/properties/location',
                'type': 'string',
                'title': 'Component location',
                'default': '',
                'examples': [
                    'Richard\'s PC'
                ]
            },
            'type': {
                '$id': '#/properties/type',
                'type': 'string',
                'title': 'The type schema',
                'default': '',
                'examples': [
                    'generic'
                ]
            },
            'uuid': {
                '$id': '#/properties/uuid',
                'type': 'null',
                'title': 'The uuid schema',
                'default': None,
            },

            'ws_url': {
                '$id': '#/properties/ws_url',
                'type': 'string',
                'title': 'The ws_url schema',
                'default': '',
                'examples': [
                    'https://villas.k8s.eonerc.rwth-aachen.de/'
                    'ws/relay/generic_1'
                ]
            },
            'api_url': {
                '$id': '#/properties/api_url',
                'type': 'string',
                'title': 'The api_url schema',
                'default': '',
                'examples': [
                    'https://villas.k8s.eonerc.rwth-aachen.de/api/ic/generic_1'
                ]
            },

            'shell': {
                '$id': '#/properties/shell',
                'type': 'boolean',
                'title': 'The shell schema',
                'default': False,
                'examples': [
                    True
                ]
            },
            'whitelist': {
                '$id': '#/properties/whitelist',
                'type': 'array',
                'title': 'The whitelist schema',
                'default': [],
                'examples': [
                    [
                        '/sbin/ping',
                        '^echo'
                    ]
                ],
                'additionalItems': True,
                'items': {
                    '$id': '#/properties/whitelist/items',
                    'anyOf': [
                        {
                            '$id': '#/properties/whitelist/items/anyOf/0',
                            'type': 'string',
                            'title': 'The first anyOf schema',
                            'default': '',
                            'examples': [
                                '/sbin/ping',
                                '^echo'
                            ]
                        }
                    ]
                }
            }
        },
        'additionalProperties': True
    }

    def create(self, message):
        component = Component.from_dict(message.payload.get('parameters'))

        try:
            self.add_component(component)
        except KeyError:
            self.logger.error('A component with the UUID %s already exists',
                              component.uuid)

    def delete(self, message):
        parameters = message.payload.get('parameters')
        uuid = parameters.get('uuid')

        try:
            comp = self.components[uuid]

            self.remove_component(comp)

        except KeyError:
            self.logger.error('There is not component with UUID: %s', uuid)
