"""Use Grover search to find unfrustrated bond configurations of a fully connected spin glass."""

import itertools as it
import subprocess
import sys
from pathlib import Path

from qiskit import QuantumCircuit, QuantumRegister, transpile
from qiskit.circuit import Gate
from qiskit_aer import AerSimulator

# Number of Grover iterations per system size, found by trial and error.
# TODO: use quantum counting to find the number of solutions and derive this.
LOOP_DICT = {3: 6, 4: 6, 5: 24}
MIN_PROBABILITY = 1e-4
SGVIZ = Path(__file__).with_name("SGViz.py")


def main():
    n = ask_num_spins()
    bonds = list(it.combinations(range(n), 2))
    qc = build_circuit(n, bonds)

    if ask_yes_no("Print circuit?"):
        print(qc.draw())
    if ask_yes_no("Save circuit as png?"):
        filename = f"N{n}_frust_qc.png"
        qc.draw(output="mpl", filename=filename, style="iqp")
        print(f"Saved to {Path(filename).resolve()}")

    print("Simulating quantum circuit...")
    solutions = find_solutions(qc, n, len(bonds))

    print("Bond configurations with no frustration, and the spin states that solve them:")
    for bond_config, (probability, spin_states) in solutions.items():
        print(f"  {bond_config}  p={probability:.4f}  spins: {', '.join(spin_states)}")

    # Give the option to visualize bond configurations using SGViz.py
    example = next(iter(solutions))
    while True:
        bond_config = input(
            f"Bond configuration to visualize (e.g. {example}), or q to quit: "
        ).strip()
        if bond_config.lower() in ("q", "quit"):
            print("Goodbye!")
            break
        if bond_config in solutions:
            subprocess.run(
                [sys.executable, SGVIZ, "-loadBC", "-BC", bond_config, "-N", str(n)]
            )
        else:
            print("Not one of the configurations above.")


def ask_num_spins() -> int:
    while True:
        answer = input("Number of spins/qubits: ")
        if answer.isdigit() and int(answer) in LOOP_DICT:
            return int(answer)
        print(f"Unable to calculate for this size. Possible sizes: {list(LOOP_DICT)}")


def ask_yes_no(question: str) -> bool:
    while True:
        answer = input(f"{question} (y/n) ").strip().lower()
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Invalid input")


def build_circuit(n: int, bonds: list[tuple[int, int]]) -> QuantumCircuit:
    spin_qubits = QuantumRegister(n, name="spin")
    bond_qubits = QuantumRegister(len(bonds), name="bond")
    multi_control_qubit = QuantumRegister(1, name="multi")
    qc = QuantumCircuit(spin_qubits, bond_qubits, multi_control_qubit)

    # Initialize multi control qubit to |->
    qc.x(multi_control_qubit)
    qc.h(multi_control_qubit)
    qc.barrier()

    # Put spin and bond qubits in equal superposition |++...+>
    qc.h(spin_qubits)
    qc.h(bond_qubits)
    qc.barrier()

    diffuser_gate = diffuser(len(bonds))
    for _ in range(LOOP_DICT[n]):
        # The oracle adds a negative phase only to solutions
        sg_oracle(qc, bonds, spin_qubits, bond_qubits, multi_control_qubit)
        qc.barrier()
        # The diffuser reflects the state vector about the equal superposition
        qc.append(diffuser_gate, bond_qubits)

    return qc


def find_solutions(
    qc: QuantumCircuit, n: int, num_bonds: int
) -> dict[str, tuple[float, list[str]]]:
    """Simulate the circuit and group likely outcomes by bond configuration.

    Returns {bond_config: (total probability, [spin states])}. Bitstrings are
    little-endian, so the leftmost bond bit is the last bond.
    """
    backend = AerSimulator(method="statevector")
    qc = qc.copy()
    qc.save_statevector()
    state = backend.run(transpile(qc, backend)).result().get_statevector()

    solutions = {}
    for key, probability in state.probabilities_dict(range(n + num_bonds)).items():
        if probability > MIN_PROBABILITY:
            bond_config, spin_state = key[:num_bonds], key[num_bonds:]
            total, spin_states = solutions.get(bond_config, (0.0, []))
            solutions[bond_config] = (total + probability, spin_states + [spin_state])
    return solutions


def diffuser(num_qubits: int) -> Gate:
    qc = QuantumCircuit(num_qubits)
    # |s> -> |00..0> -> |11..1>
    qc.h(range(num_qubits))
    qc.x(range(num_qubits))
    # Multi-controlled Z
    qc.h(num_qubits - 1)
    qc.mcx(list(range(num_qubits - 1)), num_qubits - 1)
    qc.h(num_qubits - 1)
    # |11..1> -> |00..0> -> |s>
    qc.x(range(num_qubits))
    qc.h(range(num_qubits))

    gate = qc.to_gate()
    gate.name = "$U_s$"
    return gate


def xor(qc: QuantumCircuit, a, b, output):
    qc.cx(a, output)
    qc.cx(b, output)
    qc.barrier()


def sg_oracle(
    qc: QuantumCircuit,
    bonds: list[tuple[int, int]],
    spin_qubits: QuantumRegister,
    bond_qubits: QuantumRegister,
    multi_control_qubit: QuantumRegister,
):
    # bond_i ^= spin_a XOR spin_b, for each bond i connecting spins a and b
    for (a, b), bond in zip(bonds, bond_qubits):
        xor(qc, spin_qubits[a], spin_qubits[b], bond)

    # Flip the multi control qubit (in |->) if all bonds are satisfied,
    # adding a negative phase to solutions only
    qc.mcx(bond_qubits, multi_control_qubit)

    # Uncompute to return the bond qubits to their original state
    for (a, b), bond in zip(bonds, bond_qubits):
        xor(qc, spin_qubits[a], spin_qubits[b], bond)


if __name__ == "__main__":
    main()
