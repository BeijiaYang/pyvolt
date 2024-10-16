import logging
from pathlib import Path
import numpy as np
import cimpy
import os
from scipy.io import savemat

# 1. Load CIM XML Files
this_file_folder = Path(__file__).parents[2]
p = str(this_file_folder) + "/examples/sample_data/testxml"
xml_path = Path(p)

xml_files = [os.path.join(xml_path, "1.xml"),
             os.path.join(xml_path, "2.xml"),
             os.path.join(xml_path, "3.xml")]

# Read CIM files and create new network.System object
try:
    res = cimpy.cim_import(xml_files, "cgmes_v2_4_15")
    parsed_data = res['topology']  # Extract parsed topology data
    # print(parsed_data)  # Debug output
except Exception as e:
    logging.error(f"Failed to load CIM files: {e}")
    raise

# 2. Initialize MATPOWER Case Structure
mpc = {
    'version': '2',       # MATPOWER version
    'baseMVA': 100,       # System MVA base
    'bus': [],            # List to hold bus data
    'gen': [],            # List to hold generator data
    'branch': []          # List to hold branch data
}

# 3. Extract Buses from CIM
if 'ConnectivityNode' in parsed_data:
    for node in parsed_data['ConnectivityNode']:
        bus_id = node.get('rdf:ID', "UnknownID")
        bus_name = node.get('IdentifiedObject.name', "Unknown")
        
        # Default voltage level
        voltage_level = node.get('BaseVoltage.nominalVoltage', 110)  # Adjust as needed
        
        # Fill MATPOWER bus format:
        mpc['bus'].append([bus_id, 1, 0, 0, 0, 0, 1, 1.0, 0.0, voltage_level, 1, 1.05, 0.95])
else:
    logging.warning("No 'ConnectivityNode' found in parsed data.")

# 4. Extract Generators from CIM (SynchronousMachines)
if 'SynchronousMachine' in parsed_data:
    for gen in parsed_data['SynchronousMachine']:
        bus_id = gen.get('ConnectivityNode')  # Find the bus the generator is connected to
        Pg = gen.get('P', 0)  # Active power output
        Qg = gen.get('Q', 0)  # Reactive power output
        
        # MATPOWER generator format:
        mpc['gen'].append([bus_id, Pg, Qg, 100, -100, 1.0, 100, 1, Pg * 1.2, Pg * 0.5])
else:
    logging.warning("No 'SynchronousMachine' found in parsed data.")

# 5. Extract Branches from CIM (ACLineSegment or PowerTransformer)
if 'ACLineSegment' in parsed_data:
    for line in parsed_data['ACLineSegment']:
        from_bus = line.get('Terminal.ConductingEquipment')  # Get from bus from terminal
        to_bus = line.get('Terminal.ConnectivityNode')       # Get to bus from terminal
        r = line.get('r', 0)  # Line resistance
        x = line.get('x', 0)  # Line reactance
        
        # MATPOWER branch format:
        mpc['branch'].append([from_bus, to_bus, r, x, 0.0, 250, 250, 250, 0, 0, 1])
else:
    logging.warning("No 'ACLineSegment' found in parsed data.")

# 6. Save as MATPOWER Case
savemat("mpc_case.mat", {"mpc": mpc})
