# Copyright 2018 The Cirq Developers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Union

import abc

import cirq
from cirq import circuits, devices, ops, schedules
from cirq.contrib.acquaintance.gates import (
    AcquaintanceOpportunityGate, SwapNetworkGate)
from cirq.contrib.acquaintance.bipartite import (
    BipartiteSwapNetworkGate)
from cirq.contrib.acquaintance.shift_swap_network import (
    ShiftSwapNetworkGate)
from cirq.contrib.acquaintance.permutation import (
    PermutationGate)


class AcquaintanceDevice(devices.Device, metaclass=abc.ABCMeta):
    """A device that contains only acquaintance and permutation gates.

    Raises:
        NotImplementedError: Any of the schedule-related methods (duration_of,
            validate_schedule[d_operation]) is called.
    """
    gate_types = (AcquaintanceOpportunityGate, PermutationGate)

    def validate_operation(self, operation: 'cirq.Operation') -> None:
        if not (isinstance(operation, ops.GateOperation) and
                isinstance(operation.gate, self.gate_types)):
            raise ValueError(
                    'not (isinstance({0!r}, {1!r}) and '
                          'ininstance({0!r}.gate, {2!r})'.format(
                        operation, ops.Operation, self.gate_types))

    def duration_of(self, operation):
        raise NotImplementedError()

    def validate_scheduled_operation(
            self,
            schedule: schedules.Schedule,
            scheduled_operation: schedules.ScheduledOperation
    ) -> None:
        raise NotImplementedError()


    def validate_schedule(self, schedule: schedules.Schedule) -> None:
        raise NotImplementedError()


def is_acquaintance_strategy(circuit: 'cirq.Circuit'):
    return isinstance(circuit._device, AcquaintanceDevice)

def get_acquaintance_size(obj: Union[circuits.Circuit, ops.Operation]) -> int:
    """The maximum number of qubits to be acquainted with each other."""
    if isinstance(obj, circuits.Circuit):
        if not is_acquaintance_strategy(obj):
            raise TypeError('not is_acquaintance_strategy(circuit)')
        return max(tuple(get_acquaintance_size(op)
                         for op in obj.all_operations()) or (0,))
    if not isinstance(obj, ops.Operation):
        raise TypeError('not isinstance(obj, (Circuit, Operation))')
    if not isinstance(obj, ops.GateOperation):
        return 0
    if isinstance(obj.gate, AcquaintanceOpportunityGate):
        return len(obj.qubits)
    if isinstance(obj.gate, BipartiteSwapNetworkGate):
        return 2
    if isinstance(obj.gate, ShiftSwapNetworkGate):
        return obj.gate.acquaintance_size()
    if isinstance(obj.gate, SwapNetworkGate):
        if obj.gate.acquaintance_size is None:
            return sum(sorted(obj.gate.part_lens)[-2:])
        if (obj.gate.acquaintance_size - 1) in obj.gate.part_lens:
            return obj.gate.acquaintance_size
    sizer = getattr(obj.gate, '_acquaintance_size_', None)
    return 0 if sizer is None else sizer(len(obj.qubits))

class _UnconstrainedAcquaintanceDevice(AcquaintanceDevice):
    "An acquaintance device with no constraints other than of the gate types."

    def __repr__(self):
        return 'UnconstrainedAcquaintanceDevice'  # coverage: ignore


UnconstrainedAcquaintanceDevice = _UnconstrainedAcquaintanceDevice()
