### Written by Abraham Asfaw, IBM Quantum
### Part of talk given at IEEE Quantum Week 2020
### See https://qiskit.org/textbook/ch-algorithms/grover.html for implementation details

import numpy as np
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister, Aer, execute
from qiskit.quantum_info import Operator, Statevector
from qiskit.visualization import plot_histogram

def search_steps(given_quantum_box, n_trials = 0):

	num_qubits = given_quantum_box.get_number_of_qubits()

	grover_circuit = QuantumCircuit(num_qubits)
	grover_circuit.h(grover_circuit.qubits)

	diffusion_operator = get_diffusion_circuit(num_qubits)

	for _ in range(n_trials):
		grover_circuit.compose(given_quantum_box.get_oracle(), qubits=grover_circuit.qubits, inplace=True)
		grover_circuit.compose(diffusion_operator, qubits=grover_circuit.qubits, inplace=True)

	return grover_circuit

def find_number_in_quantum_box(given_quantum_box, show_results = False, num_shots = 100):

	num_qubits = given_quantum_box.get_number_of_qubits()

	grover_circuit = QuantumCircuit(num_qubits)
	grover_circuit.h(grover_circuit.qubits)

	n_trials = int(np.floor(np.pi/4 * (2**num_qubits)**0.5))

	diffusion_operator = get_diffusion_circuit(num_qubits)

	for _ in range(n_trials):
		grover_circuit.compose(given_quantum_box.get_oracle(), qubits=grover_circuit.qubits, inplace=True)
		grover_circuit.compose(diffusion_operator, qubits=grover_circuit.qubits, inplace=True)

	grover_circuit.measure_all()
	if show_results:
		counts = execute(grover_circuit, backend=Aer.get_backend('qasm_simulator'), shots=num_shots).result().get_counts()
		for count in counts:
			print(f'Result {int(count, 2) + 1} with probability {counts[count]*100./num_shots}%')

	else:
		return grover_circuit

def get_diffusion_circuit(num_qubits):

	thiscircuit = QuantumCircuit(num_qubits)

	thiscircuit.h(thiscircuit.qubits)
	thiscircuit.x(thiscircuit.qubits)

	thiscircuit.h(num_qubits-1)
	thiscircuit.mct(list(range(num_qubits-1)), num_qubits-1)
	thiscircuit.h(num_qubits-1)

	thiscircuit.x(thiscircuit.qubits)
	thiscircuit.h(thiscircuit.qubits)

	return thiscircuit


class classical_box:

	def __init__(self, upper_bound, print_self = False):
		self.marked_number = np.random.randint(1, high=upper_bound+1, dtype=int)
		self._how_many_times_ = 0
		if print_self:
			print(f"This is a classical box containing the marked number {self.marked_number}.")

	def is_this_it(self, guess_int, verbose = False):
		self._how_many_times_ += 1
		is_match = False
		if guess_int == self.marked_number:
			is_match = True

		return is_match

	def how_many_times_invoked(self):
		return self._how_many_times_


class quantum_box:

	def __init__(self, upper_bound, print_self = False):
		self.marked_number = np.random.randint(1, high=upper_bound+1, dtype=int)
		self.num_qubits = int(np.ceil(np.log2(upper_bound)))
		self._how_many_times_ = 0
		self.oracle = self.setup_oracle()
		if print_self:
			print(f"This is a quantum box containing the marked number {self.marked_number}.")


	def is_this_it(self, guess_int, num_shots=100):
		self._how_many_times_ += 1

		binary_string = format(guess_int - 1, f'0{self.num_qubits}b')

		thiscircuit = QuantumCircuit(self.num_qubits + 1, 1)
		for ii, bit in enumerate(binary_string[::-1]):
			if bit == '1':
				thiscircuit.x(ii + 1)

		thiscircuit.h(0)
		thiscircuit.compose(self.oracle.control(), qubits=thiscircuit.qubits, inplace=True)
		thiscircuit.h(0)
		thiscircuit.measure([0], [0])
		counts = execute(thiscircuit, backend=Aer.get_backend('qasm_simulator'), shots=num_shots).result().get_counts()
		is_match = False
		if '1' in counts:
			if counts['1']*100./num_shots > 90.:
				is_match = True
		return is_match


	def how_many_times_invoked(self):
		return self._how_many_times_

	def setup_oracle(self):

		marked_number_binary = format(self.marked_number - 1, f'0{self.num_qubits}b')[::-1]
		list_of_unmarked = [i for i in range(len(marked_number_binary)) if marked_number_binary[i] == '0']
		
		thiscircuit = QuantumCircuit(self.num_qubits, name='quantum_box')
		if len(list_of_unmarked) > 0: thiscircuit.x(list_of_unmarked)
		thiscircuit.h(thiscircuit.qubits[-1])
		thiscircuit.mct(thiscircuit.qubits[:-1], thiscircuit.qubits[-1])
		thiscircuit.h(thiscircuit.qubits[-1])
		if len(list_of_unmarked) > 0: thiscircuit.x(list_of_unmarked)

		thiscircuit = thiscircuit.to_gate()
		thiscircuit.name = "Quantum Box"

		return thiscircuit


	def get_oracle(self):
		self._how_many_times_ += 1
		return self.oracle

	def get_number_of_qubits(self):
		return self.num_qubits