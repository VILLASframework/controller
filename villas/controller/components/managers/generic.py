# SPDX-FileCopyrightText: 2014-2025 The VILLASframework Authors
# SPDX-License-Identifier: Apache-2.0

from villas.controller.components.manager import Manager
from villas.controller.component import Component


class GenericManager(Manager):

    def create(self, payload):
        component = Component.from_dict(payload.get('parameters'))

        try:
            self.add_component(component)
        except KeyError:
            self.logger.error('A component with the UUID %s already exists',
                              component.uuid)

    def delete(self, payload):
        parameters = payload.get('parameters')
        uuid = parameters.get('uuid')

        try:
            comp = self.components[uuid]

            self.remove_component(comp)

        except KeyError:
            self.logger.error('There is not component with UUID: %s', uuid)
