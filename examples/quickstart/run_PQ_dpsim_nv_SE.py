import logging
from pathlib import Path
from pyvolt import network
from pyvolt import nv_powerflow
from pyvolt import results
import numpy
import cimpy
import os
import dpsimpy
# from villas.dataprocessing.readtools import *
# from villas.dataprocessing.timeseries import *
# import villas.dataprocessing.validationtools as validationtools


# Basic logger configuration
logging.basicConfig(filename='run_nv_powerflow.log', level=logging.INFO, filemode='w')

# __file__: path of current file
# pathlib.Path(__file__): returns the file path object 
# .parents: root path up to 2 (here up to pyvolt/)
this_file_folder =  Path(__file__).parents[2]
p = str(this_file_folder)+"/examples/sample_data/CIGRE-MV-NoTap"
xml_path = Path(p)

xml_files = [os.path.join(xml_path, "Rootnet_FULL_NE_06J16h_DI.xml"),
             os.path.join(xml_path, "Rootnet_FULL_NE_06J16h_EQ.xml"),
             os.path.join(xml_path, "Rootnet_FULL_NE_06J16h_SV.xml"),
             os.path.join(xml_path, "Rootnet_FULL_NE_06J16h_TP.xml")]
# print(xml_files)

# Read cim files by dpsimpy.CIMReader
sim_name = 'Rootnet_FULL_NE'
reader = dpsimpy.CIMReader(sim_name)
system_dpsim = reader.loadCIM(50, xml_files, dpsimpy.Domain.SP, dpsimpy.PhaseType.Single, dpsimpy.GeneratorType.PVNode)

# Run DPsim simulation
sim = dpsimpy.Simulation(sim_name)
sim.set_system(system_dpsim)
sim.set_domain(dpsimpy.Domain.SP)
sim.set_solver(dpsimpy.Solver.NRP)
# sim.set_time_step(1)
# sim.set_final_time(10)

logger = dpsimpy.Logger(sim_name)
for node in system_dpsim.nodes:
    logger.log_attribute(node.name(),      'v', node)
    # logger.log_attribute(node.name()+"_S", 's', node)
sim.add_logger(logger)
sim.run()

# # list of system objects
# print(system_dpsim.list_idobjects())

# # Read DPim results
# path = '/home/bya/github/pyvolt/examples/quickstart/logs/'
# dpsim_result_file = path + sim_name + '.csv'

# ts_dpsim = read_timeseries_csv(dpsim_result_file)

# # Fix for dpsim naming - TODO: unify dpsim notation in log file and update villas-dataprocessing accordingly
# for ts,values in ts_dpsim.items():
#     values.name = values.name[:-2]
#     print(ts, values.values)


# Read DPsim logger file to create a Results(), but firstly create a pyvolt topology
# Read cim files and create new network.System object
cim_topo = cimpy.cim_import(xml_files, "cgmes_v2_4_15")
system_pyvolt = network.System()
base_apparent_power = 25  # MW
system_pyvolt.load_cim_data(cim_topo['topology'], base_apparent_power)

dpsim_result_file = os.path.realpath(os.path.join(this_file_folder,
                                                    "examples",
                                                    "quickstart",
                                                    "logs",
                                                    "Rootnet_FULL_NE.csv"))

result = results.Results(system_pyvolt)
result.read_data(dpsim_result_file)
result.calculate_all()

for node in result.nodes:
    print("\t", node.voltage, "\t", node.power)


####
# let the dpsim log the correct power
# upgrade result.read_data(), now it only reads voltage
### 
