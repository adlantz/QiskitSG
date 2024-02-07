# initialization
import itertools as it
import os
from typing import List


# importing Qiskit
from qiskit import (
    Aer,
    QuantumCircuit,
    ClassicalRegister,
    QuantumRegister,
    transpile,
)


# import basic plot tools
from qiskit.visualization import plot_histogram

import pprint


LOOP_DICT = {3: 6, 4: 6, 5: 24}


def main():
    # Get number of spins
    while True:
        N = int(input("Number of spins/qubits: "))
        if N in LOOP_DICT:
            break
        print(
            f"Unable to calculate for this size. Possible sizes: {list(LOOP_DICT.keys())}"
        )

    bond_list = bond_list_maker(N)
    num_of_bonds = len(bond_list)

    # Build requisite quantum and classical registers
    spin_qubits = QuantumRegister(N, name="spin")
    bond_qubits = QuantumRegister(num_of_bonds, name="bond")
    multi_control_qubit = QuantumRegister(1, name="multi")
    cbits = ClassicalRegister(num_of_bonds, name="cbit")
    qc = QuantumCircuit(spin_qubits, bond_qubits, multi_control_qubit, cbits)

    # Initialize multi control qubit to |-> state
    qc.x(multi_control_qubit)
    qc.h(multi_control_qubit)
    qc.barrier()  # for visual separation

    # Initialise spin and bond qubits in state |++...+> (equal superposition)
    qc.h(spin_qubits)
    qc.h(bond_qubits)
    qc.barrier()

    # We don't know how many solutions there are so we can't calculate the optimal number of loops
    # TODO: Implement quantum counting to find number of solutions
    # Until we implement the above, we just use the LOOP_DICT dictionary I made from trial and error

    loop_number = LOOP_DICT[N]

    for _ in range(loop_number):
        # Add the oracle - this adds a negative phase only to solutions
        SG_oracle(qc, bond_list, bond_qubits, multi_control_qubit)
        qc.barrier()
        # Add the diffuser, this "reflects" the state vector around the equal superposition vector
        # We make this a gate for legibility
        qc.append(diffuser(num_of_bonds), bond_qubits)

    # print(qc.draw())

    # Measure the variable qubits
    # qc.measure(bond_qubits, cbits)

    # Print/Save circuit interface
    while True:
        prntqc = input("Print Circuit? (y/n)")
        if prntqc == "y" or prntqc == "yes":
            print(qc.draw())
            break
        elif prntqc.lower() in ("n", "no"):
            break
        else:
            print("invalid input")

    while True:
        sveqc = input("Save circuit as png? (y/n)")
        if sveqc == "y" or sveqc == "yes":
            print("saving to " + str(os.getcwd()))
            qc.draw(output="mpl", filename="N" + str(N) + "_frust_qc.png", style="iqp")
            break
        elif sveqc.lower() in ("n", "no"):
            break
        else:
            print("invalid input")

    print("Simulating quantum circuit...")

    # Send circuit to backend to get exact mathematical state of circuit before measuring
    backend = Aer.get_backend("aer_simulator_statevector")
    qc.save_statevector()
    result = backend.run(transpile(qc, backend)).result()
    final_state_vector = result.get_statevector(qc)

    # Get probabilities of each bond + spin state combo
    probabilities_dict = final_state_vector.probabilities_dict(
        [i for i in range(N + num_of_bonds)]
    )

    # Consolidate most probable bonds and their solution spin states
    output_obj = {}
    for key in probabilities_dict:
        if probabilities_dict[key] > 0.0001:
            bond_state = key[:num_of_bonds]
            spin_sate = key[0 - N :]
            if bond_state not in output_obj:
                output_obj[bond_state] = {
                    "probability": probabilities_dict[key],
                    "spin_states": [spin_sate],
                }
            else:
                output_obj[bond_state]["probability"] += probabilities_dict[key]
                output_obj[bond_state]["spin_states"].append(spin_sate)

    print(
        "Here are the bond states with no frustration and the spin states that solve them"
    )
    pprint.PrettyPrinter(indent=4).pprint(output_obj)

    # Give the option to visualize bond configurations using SGViz.py
    while True:
        bond_config = input(
            f"Input bond configuration from keys of object above (Example: {list(output_obj.keys())[0]}) to visualize (q to to quit): "
        )
        if bond_config.lower() in ("q", "quit"):
            print("Goodbye!")
            break
        if bond_config in output_obj:
            os.system("python3 SGViz.py -loadBC -BC " + bond_config + " -N " + str(N))
        else:
            print("not a valid input")


def bond_list_maker(N: int) -> List[List[int]]:
    # Given a set of spins, an ordered list of the form [ [a,b], [a,c], ...] where
    # the ith element is a list of the two spins connected by the ith bond
    return [list(c) for c in it.combinations([i for i in range(N)], 2)]


def diffuser(nqubits: int):
    qc = QuantumCircuit(nqubits)
    # Apply transformation |s> -> |00..0> (H-gates)
    for qubit in range(nqubits):
        qc.h(qubit)
    # Apply transformation |00..0> -> |11..1> (X-gates)
    for qubit in range(nqubits):
        qc.x(qubit)
    # Do multi-controlled-Z gate
    qc.h(nqubits - 1)
    qc.mcx(list(range(nqubits - 1)), nqubits - 1)  # multi-controlled-toffoli
    qc.h(nqubits - 1)
    # Apply transformation |11..1> -> |00..0>
    for qubit in range(nqubits):
        qc.x(qubit)
    # Apply transformation |00..0> -> |s>
    for qubit in range(nqubits):
        qc.h(qubit)
    # Return the diffuser as a gate
    U_s = qc.to_gate()
    U_s.name = "$U_s$"
    return U_s


def XOR(qc, a, b, output):
    qc.cx(a, output)
    qc.cx(b, output)
    qc.barrier()


def SG_oracle(
    qc: QuantumCircuit,
    bond_list: List[List[int]],
    bond_qubits: QuantumRegister,
    multi_control_qubit: QuantumRegister,
):
    # Add an XOR to each bond qubit such that if bond_i connects spin_a
    # and spin_b, the bond_i qubit will become spin_a XOR spin_b
    for i, clause in enumerate(bond_list):
        XOR(qc, clause[0], clause[1], bond_qubits[i])

    # Apply X gate to 'multicontrol' qubit if all clauses are satisfied
    # This adds a negative phase to solution items only
    qc.mcx(bond_qubits, multi_control_qubit)

    # Add the exact same XOR gates to "uncompute" and return bonds to original state
    for i, clause in enumerate(bond_list):
        XOR(qc, clause[0], clause[1], bond_qubits[i])
        i += 1


if __name__ == "__main__":
    main()
