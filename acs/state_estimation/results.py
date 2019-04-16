import numpy as np
import cmath

import sys
sys.path.append("../../../dataprocessing")
from villas.dataprocessing.readtools import *

class ResultsNode():
	def __init__(self, topo_node):		
		self.topology_node = topo_node		
		self.voltage = complex(0, 0)		
		self.current = complex(0, 0)
		self.power = complex(0, 0)

class ResultsBranch():
	def __init__(self, topo_branch):
		self.topology_branch = topo_branch
		self.current = complex(0, 0)
		self.power = complex(0, 0)			#complex power flow at branch, measured at initial node
		self.power2 = complex(0, 0)			#complex power flow at branch, measured at final node 
		
class Results():	
	def __init__(self, system):
		self.nodes=[]
		self.branches=[]
		self.Ymatrix=system.Ymatrix
		self.Adjacencies=system.Adjacencies
		for node in system.nodes:
			self.nodes.append(ResultsNode(topo_node=node))
		for branch in system.branches:
			self.branches.append(ResultsBranch(topo_branch=branch))
			
	def read_data_dpsim(self, file_name):
		"""
		read the voltages from a dpsim input file
		"""
		loadflow_results = read_timeseries_dpsim(file_name, print_status=False)
		for node in self.nodes:
			node.voltage = loadflow_results[node.topology_node.uuid].values[0]

	def load_voltages(self, V):
		"""
		load the voltages of V-array (result of powerflow_cim.solve)
		"""
		for index in range(len(V)):
			for elem in self.nodes:
				if elem.topology_node.index == index:
					elem.voltage = V[index]

	def calculate_all(self):
		"""
		calculate all quantities of the grid
		"""
		self.calculateI()
		self.calculateIinj()
		self.calculateSinj()
		self.calculateIinj()
		self.calculateS1()
		self.calculateS2()

	def calculateI(self):
		"""
		To calculate the branch currents
		"""	
		for branch in self.branches:
			fr = branch.topology_branch.start_node.index
			to = branch.topology_branch.end_node.index
			branch.current = - (self.nodes[fr].voltage - self.nodes[to].voltage)*self.Ymatrix[fr][to]
	
	def calculateIinj(self):
		"""
		calculate current injections at a node
		"""
		for node in self.nodes:
			to=complex(0, 0)	#sum of the currents flowing to the node
			fr=complex(0, 0)	#sum of the currents flowing from the node
			for branch in self.branches:
				if node.topology_node.index==branch.topology_branch.start_node.index:
					fr = fr + branch.current
				if node.topology_node.index==branch.topology_branch.end_node.index:
					to = to + branch.current
			node.current = to - fr
	
	def calculateSinj(self):
		"""
		calculate power injection at a node
		"""
		for node in self.nodes:
			node.power = node.voltage*np.conj(node.current)
	
	def calculateS1(self):
		"""
		calculate complex power flow at branch, measured at initial node
		"""
		for branch in self.branches:
			branch_index = branch.topology_branch.start_node.index
			for node in self.nodes:
				if branch_index == node.topology_node.index:
					branch.power = node.voltage*(np.conj(branch.current))
	
	def calculateS2(self):
		"""
		calculate complex ower flow at branch, measured at final node 
		"""
		for branch in self.branches:
			branch_index = branch.topology_branch.end_node.index
			for node in self.nodes:
				if branch_index == node.topology_node.index:
					branch.power2 = -node.voltage*(np.conj(branch.current))
	
	def get_node(self, index=None, uuid=None):
		"""
		return the PowerflowNode with PowerflowNode.topology_node.index == index
		returns a node with a certain uuid or a certain index (not both!):
		- if index in not None --> return the PowerflowNode with PowerflowNode.topology_node.index == index
		- if uuid in not None --> return the PowerflowNode with PowerflowNode.topology_node.uuid == uuid
		"""
		if index is not None:
			for node in self.nodes:
				if index == node.topology_node.index:
					return node
		elif uuid is not None:
			for node in self.nodes:
				if uuid == node.topology_node.uuid:
					return node
				
	def get_voltages(self):
		"""
		get node voltages
		for a test purpose
		"""
		voltages = np.zeros(len(self.nodes), dtype=np.complex_)
		for node in self.nodes:
			voltages[node.topology_node.index] = node.voltage
		return voltages
	
	def get_Iinj(self):
		"""
		get node currents 
		for a test purpose
		"""
		Iinj = np.zeros(len(self.nodes), dtype=np.complex_)
		for node in self.nodes:
			Iinj[node.topology_node.index] = node.current
		return Iinj
		
	def get_Sinj(self):
		"""
		get node power 
		for a test purpose
		"""
		Sinj = np.zeros(len(self.nodes), dtype=np.complex_)
		for node in self.nodes:
			Sinj[node.topology_node.index] = node.power
		return Sinj
		
	
	def getI(self):
		"""
		get branch currents 
		for a test purpose
		"""
		I = np.array([])
		for branch in self.branches:
			I = np.append(I, branch.current)
		return I
		
	def get_S1(self):
		"""
		get complex Power flow at branch, measured at initial node
		for a test purpose
		"""
		S1 = np.array([])
		for branch in self.branches:
			S1 = np.append(S1, branch.power)
		return S1
		
	def get_S2(self):
		"""
		get complex Power flow at branch, measured at final node  
		for a test purpose
		"""
		S2 = np.array([])
		for branch in self.branches:
			S2 = np.append(S2, branch.power2)
		return S2

	def print_voltages_polar(self):
		"""
		for test purposes
		"""
		for node in self.nodes:
			print(node.topology_node.uuid + ": " + str(cmath.polar(node.voltage)))