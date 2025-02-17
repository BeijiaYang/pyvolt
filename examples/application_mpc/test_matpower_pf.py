import logging
from pathlib import Path
from pyvolt import network
from pyvolt import nv_powerflow
import numpy
import os

from mpc_2_pyvolt import parse_case_topology
from mpc_2_pyvolt import mpc_to_pyvolt

# Basic logger configuration
logging.basicConfig(filename='test_matpower_pf.log', level=logging.INFO, filemode='w')

# Parse the matpower data
file_path = 'case_topo\case_topology.m'  
matpower_data = parse_case_topology(file_path)

# Convert to Pyvolt network
system_pyvolt = mpc_to_pyvolt(matpower_data)
base_apparent_power = 100  # MW

# Execute power flow analysis
results_pf, num_iter = nv_powerflow.solve(system_pyvolt)

# Print node voltages
print("\n---Powerflow converged in " + str(num_iter) + " iterations.---\n")
print("Results: \n")
voltages = []
for node in results_pf.nodes:
    print('{} = {} \n'.format(node.topology_node.uuid, node.voltage_pu))
    #print('{}={} \n'.format(node.topology_node.uuid, node.voltage))
    voltages.append(node.voltage_pu)