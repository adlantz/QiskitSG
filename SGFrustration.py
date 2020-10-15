#initialization
import matplotlib.pyplot as plt
import numpy as np
import itertools as it
import os



# importing Qiskit
from qiskit import IBMQ, Aer, QuantumCircuit, ClassicalRegister, QuantumRegister, execute
from qiskit.extensions.simulator import snapshot
from qiskit.providers.ibmq import least_busy
from qiskit.quantum_info import Statevector

# import basic plot tools
from qiskit.visualization import plot_histogram



def main():
    # print(J_matrix)
    N = int(input("Number of spins/qubits: "))
    clause_list = clause_list_maker(N)
    cqb = len(clause_list)
    # print(clause_list)

    # t_qubits = QuantumRegister(cqb, name='t')
    var_qubits = QuantumRegister(N, name='v')
    clause_qubits = QuantumRegister(cqb, name='c')
    output_qubit = QuantumRegister(1, name='out')
    cbits = ClassicalRegister(cqb, name='cbits')
    qc = QuantumCircuit(var_qubits, clause_qubits, output_qubit, cbits)


    # Initialise 'out0' in state |->
    qc.initialize([1, -1]/np.sqrt(2), output_qubit)

    # Initialise qubits in state |s>
    qc.h(var_qubits)
    qc.h(clause_qubits)
    # qc.h(t_qubits)
    qc.barrier()  # for visual separation


    loopdict = {3:2, 4:6, 5:24}
    if N in loopdict:
    	loopnumber = loopdict[N]
    else:
    	loopnumber = 25
    for i in range(loopnumber):
        SG_oracle(qc, clause_list, var_qubits, clause_qubits, cbits, output_qubit)
        qc.barrier()  # for visual separation
        # Apply our diffuser
        qc.append(diffuser(cqb), clause_qubits)


    # Measure the variable qubits
    # qc.measure(clause_qubits, cbits)



    
    asking=True
    while(asking):
        prntqc = input("Print Circuit? (y/n)")
        if prntqc == 'y' or prntqc == 'yes':
            print(qc.draw())
            asking = False
        elif prntqc == 'n' or prntqc == 'no':
            asking = False
        else:
            print("invalid input")
    
    asking=True
    while(asking):
        sveqc = input("Save circuit as png? (y/n)")
        if sveqc == 'y' or sveqc == 'yes':
            print("saving to " + str(os.getcwd()))
            qc.draw(output='mpl',filename="N" + str(N) + "_frust_qc.png")
            asking = False
        elif sveqc == 'n' or sveqc == 'no':
            asking = False
        else:
            print("invalid input")




    print("Simulating quantum circuit...")


    backend = Aer.get_backend('statevector_simulator')
    job = execute(qc, backend)
    result = job.result()
    outputstate = result.get_statevector(qc)
    probstate = np.multiply(outputstate,np.conj(outputstate)).real

    probampdict = {}
    bs = '{0:0' + str(cqb) + 'b}'
    for i in range(2**cqb):
        probampdict[bs.format(i)] = 0

    i = 0
    fbs = '{0:0' + str(cqb + N + 1) + 'b}'
    for ops in probstate:
        probampdict[fbs.format(i)[1:(cqb+1)]] += ops
        i+=1



    solpa = probampdict[bs.format((2**(cqb) - 1))]


    i=0
    j=1
    bcarray=[]
    for key in probampdict:
        if probampdict[key] > 0.9*solpa:
            print(str(j) +".",bs.format(i),probampdict[key])
            bcarray.append(bs.format(i))
            j+=1
        i+=1
    



    viz = True
    invld = False
    while(viz):
        index = input("Visualize circuit (input number of configuration from list above or q to quit): ")
        try:
            int(index)
            invld= False
        except:
            invld = True
        if index == 'q' or index == 'quit':
            break
        elif invld:
            print("Invalid input")
        elif int(index) <= len(bcarray):
            os.system("python3 SGViz.py -loadBC -BC " + str(bcarray[int(index)-1]) + " -N " + str(N))
        else:
            print("not a valid index")
    

    print("Goodbye")

def initialize_s(qc, qubits):
    """Apply a H-gate to 'qubits' in qc"""
    for q in qubits:
        qc.h(q)
    return qc

def clause_list_maker(N):
    return np.array([np.array(list(c)) for c in it.combinations([i for i in range(N)],2)])


def diffuser(nqubits):
    qc = QuantumCircuit(nqubits)
    # Apply transformation |s> -> |00..0> (H-gates)
    for qubit in range(nqubits):
        qc.h(qubit)
    # Apply transformation |00..0> -> |11..1> (X-gates)
    for qubit in range(nqubits):
        qc.x(qubit)
    # Do multi-controlled-Z gate
    qc.h(nqubits-1)
    qc.mct(list(range(nqubits-1)), nqubits-1)  # multi-controlled-toffoli
    qc.h(nqubits-1)
    # Apply transformation |11..1> -> |00..0>
    for qubit in range(nqubits):
        qc.x(qubit)
    # Apply transformation |00..0> -> |s>
    for qubit in range(nqubits):
        qc.h(qubit)
    # We will return the diffuser as a gate
    U_s = qc.to_gate()
    U_s.name = "$U_s$"
    return U_s


def XOR(qc, a, b, output):
    qc.cx(a, output)
    qc.cx(b, output)
    qc.barrier()

def XNOR(qc, a, b, output):
    qc.cx(a, output)
    qc.cx(b, output)
    qc.x(output)
    qc.barrier()

def SG_oracle(qc, clause_list, var_qubits, clause_qubits, cbits, output_qubit):
    # Compute clauses
    i = 0
    for clause in clause_list:
        XOR(qc, clause[0], clause[1], clause_qubits[i])
        i += 1

    # Flip 'output' bit if all clauses are satisfied
    qc.mct(clause_qubits, output_qubit)

    # Uncompute clauses to reset clause-checking bits to 0
    i = 0
    for clause in clause_list:
        XOR(qc, clause[0], clause[1], clause_qubits[i])
        i += 1



if __name__ == '__main__':
    main()