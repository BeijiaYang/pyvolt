import logging
from pathlib import Path
from pyvolt import network
from pyvolt import nv_powerflow
import numpy
import cimpy
import os
from villas.dataprocessing.readtools import *
from villas.dataprocessing.timeseries import *
import villas.dataprocessing.validationtools as validationtools
import dpsimpy

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

print(xml_files)

# Read cim files by dpsimpy.CIMReader
sim_name = 'Rootnet_FULL_NE'
reader = dpsimpy.CIMReader(sim_name)
system = reader.loadCIM(50, xml_files, dpsimpy.Domain.SP, dpsimpy.PhaseType.Single, dpsimpy.GeneratorType.PVNode)

# Run DPsim simulation
sim = dpsimpy.Simulation(sim_name)
sim.set_system(system)
sim.set_domain(dpsimpy.Domain.SP)
sim.set_solver(dpsimpy.Solver.NRP)

logger = dpsimpy.Logger(sim_name)
for node in system.nodes:
    logger.log_attribute(node.name()+'.V', 'v', node)
sim.add_logger(logger)

sim.run()

# Read DPim results
path = 'logs/'
dpsim_result_file = path + sim_name + '.csv'

ts_dpsim = read_timeseries_csv(dpsim_result_file)

# Fix for dpsim naming - TODO: unify dpsim notation in log file and update villas-dataprocessing accordingly
for ts,values in ts_dpsim.items():
    values.name = values.name[:-2]


