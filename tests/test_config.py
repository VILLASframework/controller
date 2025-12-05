# SPDX-FileCopyrightText: 2014-2025 The VILLASframework Authors
# SPDX-License-Identifier: Apache-2.0

from uuid import UUID

from villas.controller.config import Config


def is_valid_uuid(uuid_to_test):
    try:
        uuid_obj = UUID(uuid_to_test)
    except ValueError:
        return False
    return str(uuid_obj) == uuid_to_test


def test_is_valid_uuid():
    assert is_valid_uuid('20354d7a-e4fe-47af-8ff6-187bca92f3f9')


def test_config():
    with open('etc/config.yaml') as f:
        c = Config(f)

        assert len(c.components) == 4

        for comp in c.components:
            assert is_valid_uuid(comp.uuid)

        assert c.components[0].category == 'manager'
        assert c.components[0].type == 'generic'
        assert c.components[0].name == 'Standard Controller'
        assert c.components[0].realm == 'de.rwth-aachen.eonerc.acs'
        assert c.components[0].uuid == 'f4751894-205e-11eb-aefb-0741ff98abca'
