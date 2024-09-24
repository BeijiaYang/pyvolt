# This example will provide a test case running the state estimator.
# The state estimation is performed based on the results using the nv_powerflow implementation

import logging
from pathlib import Path
import numpy as np
from pyvolt import results
from pyvolt import network
from pyvolt import nv_powerflow
from pyvolt import nv_state_estimator
from pyvolt import measurement
import cimpy
import os


logging.basicConfig(filename='run_nv_state_estimator.log', level=logging.INFO, filemode='w')

this_file_folder = os.path.dirname(os.path.realpath(__file__))
xml_path = os.path.realpath(os.path.join(this_file_folder, "..", "sample_data", "CIGRE-MV-NoTap"))
xml_files = [os.path.join(xml_path, "Rootnet_FULL_NE_06J16h_DI.xml"),
             os.path.join(xml_path, "Rootnet_FULL_NE_06J16h_EQ.xml"),
             os.path.join(xml_path, "Rootnet_FULL_NE_06J16h_SV.xml"),
             os.path.join(xml_path, "Rootnet_FULL_NE_06J16h_TP.xml")]

# Read cim files and create new network.System object
cim_topo = cimpy.cim_import(xml_files, "cgmes_v2_4_15")
system_pyvolt = network.System()
base_apparent_power = 25  # MW
system_pyvolt.load_cim_data(cim_topo['topology'], base_apparent_power)

# Execute power flow analysis
results_pf, num_iter_cim = nv_powerflow.solve(system_pyvolt)

# --- State Estimation ---
""" Write here the percent uncertainties of the measurements"""
V_unc = 0
I_unc = 0
Sinj_unc = 0
S_unc = 0
Pmu_mag_unc = 0
Pmu_phase_unc = 0

# Create measurements data structures
"""use all node voltages as measures"""
measurements_set = measurement.MeasurementSet()
for node in results_pf.nodes:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Vpmu_mag,
                                        np.absolute(node.voltage_pu), Pmu_mag_unc)
for node in results_pf.nodes:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Vpmu_phase,
                                        np.angle(node.voltage_pu), Pmu_phase_unc)
measurements_set.meas_creation()

# Perform state estimation
state_estimation_results = nv_state_estimator.DsseCall(system_pyvolt, measurements_set)

# Read DPsim logger file to create a Results(), and compare the SE results with dpsim csv(here assumed as real voltages)
dpsim_result_file = os.path.realpath(os.path.join(this_file_folder,
                                                    "logs",
                                                    "Rootnet_FULL_NE.csv"))

result = results.Results(system_pyvolt)
result.read_data(dpsim_result_file)

# Print SE results and dpsim results(as real voltages), compare the difference and relative error rate
print("Node||  State_Estimation_results.voltages(V) ||   DPsim_simulation_results.voltages(V) ||  Difference")
print("-"*100)
for node_se, node_dpsim in zip(state_estimation_results.nodes, result.nodes):
    print(f"{node_se.topology_node.uuid}:\t{node_se.voltage*1000:<6.8f}\t\t\t{node_dpsim.voltage:<6.6f}\t\t{node_se.voltage*1000-node_dpsim.voltage:<6.6f}")


""" Write here the percent uncertainties of the measurements"""
V_unc = 0
I_unc = 0
Sinj_unc = 0
S_unc = 0
Pmu_mag_unc = 1
Pmu_phase_unc = 2

# Create new measurements data structures
"""use all node voltages as measures"""
measurements_set = measurement.MeasurementSet()
for node in results_pf.nodes:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Vpmu_mag,
                                        np.absolute(node.voltage_pu), Pmu_mag_unc)
for node in results_pf.nodes:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Vpmu_phase,
                                        np.angle(node.voltage_pu), Pmu_phase_unc)
measurements_set.meas_creation()

# Perform state estimation
state_estimation_results_new = nv_state_estimator.DsseCall(system_pyvolt, measurements_set)

# Print SE results and dpsim results(as real voltages), compare the difference and relative error rate
print("Node||  State_Estimation_results.voltages(V) ||   DPsim_simulation_results.voltages(V) ||  Difference")
print("-"*100)
for node_se, node_dpsim in zip(state_estimation_results_new.nodes, result.nodes):
    print(f"{node_se.topology_node.uuid}:\t{node_se.voltage*1000:<6.6f}\t\t\t{node_dpsim.voltage:<6.6f}\t\t{node_se.voltage*1000-node_dpsim.voltage:<6.6f}")
