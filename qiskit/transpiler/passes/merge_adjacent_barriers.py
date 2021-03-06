# -*- coding: utf-8 -*-

# Copyright 2019, IBM.
#
# This source code is licensed under the Apache License, Version 2.0 found in
# the LICENSE.txt file in the root directory of this source tree.
"""
A pass that merges any adjacent barriers into one

Only barriers which can be merged without affecting the barrier structure of the
DAG will be merged.

Not all redundant barriers will necessarily be merged, only adjacent barriers are merged.

For example, the circuit
qr = QuantumRegister(3, 'q')
circuit = QuantumCircuit(qr)
circuit.barrier(qr[0])
circuit.barrier(qr[1])
circuit.barrier(qr)

Will be transformed into a circuit corresponding to
circuit.barrier(qr[0])
circuit.barrier(qr)
after one iteration of the pass. These two barriers were not merged by the first pass as they are
not adjacent in the initial circuit.

The pass then can be reapplied to merge the newly adjacent barriers.
"""

from qiskit.transpiler.basepasses import TransformationPass
from qiskit.dagcircuit import DAGCircuit
from qiskit.extensions.standard.barrier import Barrier


class MergeAdjacentBarriers(TransformationPass):
    """Returns a circuit with any adjacent barriers merged together"""

    def run(self, dag):

        # sorted to so that they are in the order they appear in the DAG
        # so ancestors/descendants makes sense
        barriers = [nd for nd in dag.topological_op_nodes() if nd.name == 'barrier']

        # get dict of barrier merges
        node_to_barrier_qubits = MergeAdjacentBarriers._collect_potential_merges(dag, barriers)

        if not node_to_barrier_qubits:
            return dag

        # add the merged barriers to a new DAG
        new_dag = DAGCircuit()

        for qreg in dag.qregs.values():
            new_dag.add_qreg(qreg)
        for creg in dag.cregs.values():
            new_dag.add_creg(creg)

        # go over current nodes, and add them to the new dag
        for node in dag.topological_op_nodes():
            if node.name == 'barrier':
                if node in node_to_barrier_qubits:
                    qubits = node_to_barrier_qubits[node]
                    # qubits are stored as a set, need to convert to a list
                    new_dag.apply_operation_back(Barrier(len(qubits)), qargs=list(qubits))
            else:
                # copy the condition over too
                if node.condition:
                    new_dag.apply_operation_back(node.op, qargs=node.qargs, cargs=node.cargs,
                                                 condition=node.condition)
                else:
                    new_dag.apply_operation_back(node.op, qargs=node.qargs, cargs=node.cargs)
        return new_dag

    @staticmethod
    def _collect_potential_merges(dag, barriers):
        """
        Returns a dict of DAGNode : Barrier objects, where the barrier needs to be
        inserted where the corresponding DAGNode appears in the main DAG
        """
        # if only got 1 or 0 barriers then can't merge
        if len(barriers) < 2:
            return None

        # mapping from the node that will be the main barrier to the
        # barrier object that gets built up
        node_to_barrier_qubits = {}

        # Start from the first barrier
        current_barrier = barriers[0]
        end_of_barrier = current_barrier
        current_barrier_nodes = [current_barrier]

        current_qubits = set(current_barrier.qargs)
        current_ancestors = dag.ancestors(current_barrier)
        current_descendants = dag.descendants(current_barrier)

        barrier_to_add = Barrier(len(current_qubits))

        for next_barrier in barriers[1:]:

            # Remove all barriers that have already been included in this new barrier from the set
            # of ancestors/descendants as they will be removed from the new DAG when it is created
            next_ancestors = {nd for nd in dag.ancestors(next_barrier)
                              if nd not in current_barrier_nodes}
            next_descendants = {nd for nd in dag.descendants(next_barrier)
                                if nd not in current_barrier_nodes}
            next_qubits = set(next_barrier.qargs)

            if (
                    not current_qubits.isdisjoint(next_qubits)
                    and current_ancestors.isdisjoint(next_descendants)
                    and current_descendants.isdisjoint(next_ancestors)
            ):

                # can be merged
                current_ancestors = current_ancestors | next_ancestors
                current_descendants = current_descendants | next_descendants
                current_qubits = current_qubits | next_qubits

                # update the barrier that will be added back to include this barrier
                barrier_to_add = Barrier(len(current_qubits))

            else:
                # store the previously made barrier
                if barrier_to_add:
                    node_to_barrier_qubits[end_of_barrier] = current_qubits

                # reset the properties
                current_qubits = set(next_barrier.qargs)
                current_ancestors = dag.ancestors(next_barrier)
                current_descendants = dag.descendants(next_barrier)

                barrier_to_add = Barrier(len(current_qubits))
                current_barrier_nodes = []

            end_of_barrier = next_barrier
            current_barrier_nodes.append(end_of_barrier)

        if barrier_to_add:
            node_to_barrier_qubits[end_of_barrier] = current_qubits

        return node_to_barrier_qubits
