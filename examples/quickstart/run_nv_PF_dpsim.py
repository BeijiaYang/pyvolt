import logging
from pathlib import Path
from pyvolt import network
from pyvolt import nv_powerflow
import numpy
import cimpy
import os
import dpsim

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

# Read cim files and create new network.System object
res = cimpy.cim_import(xml_files, "cgmes_v2_4_15")
system = network.System()
base_apparent_power = 25  # MW
system.load_cim_data(res['topology'], base_apparent_power)

results = ["ACLineSegment", "PowerTransformer", "EnergyConsumer"]
for key, value in res["topology"].items():
    if value.__class__.__name__ in results:
        print(value.__str__())
