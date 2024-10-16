import logging
from pathlib import Path
from pyvolt import network
from pyvolt import nv_powerflow
import numpy
import cimpy
import os

# Basic logger configuration
logging.basicConfig(filename='test_PF.log', level=logging.INFO, filemode='w')

# __file__: path of current file
# pathlib.Path(__file__): returns the file path object 
# .parents: root path up to 2 (here up to pyvolt/)
this_file_folder =  Path(__file__).parents[2]
p = str(this_file_folder)+"/examples/sample_data/testxml"
xml_path = Path(p)


xml_files = [os.path.join(xml_path, "1.xml"),
             os.path.join(xml_path, "2.xml"),
             os.path.join(xml_path, "3.xml")]

# Read cim files and create new network.System object
res = cimpy.cim_import(xml_files, "cgmes_v2_4_15")
system = network.System()
base_apparent_power = 25  # MW
system.load_cim_data(res['topology'], base_apparent_power)

# Execute power flow analysis
results_pf, num_iter = nv_powerflow.solve(system)

# Print node voltages
print("\n---Powerflow converged in " + str(num_iter) + " iterations.---\n")
print("Results: \n")
voltages = []
for node in results_pf.nodes:
    print('{} = {} \n'.format(node.topology_node.uuid, node.voltage_pu))
    #print('{}={} \n'.format(node.topology_node.uuid, node.voltage))
    voltages.append(node.voltage_pu)

