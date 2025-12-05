# SPDX-FileCopyrightText: 2014-2025 The VILLASframework Authors
# SPDX-License-Identifier: Apache-2.0

class SimulationException(Exception):
    def __init__(self, sim, msg, **kwargs):
        super().__init__(sim, msg, kwargs)

        self.msg = msg
        self.info = kwargs
