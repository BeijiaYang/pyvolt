import os
import logging
import cimpy
import numpy as np

from pyvolt import network
from pyvolt import nv_powerflow
from pyvolt import nv_state_estimator
from pyvolt import measurement
from pyvolt import results


logging.basicConfig(filename='test_nv_powerflow.log', level=logging.INFO, filemode='w')

this_file_folder = os.path.dirname(os.path.realpath(__file__))
xml_path = os.path.realpath(os.path.join(this_file_folder, "..", "sample_data", "CIGRE-MV-NoTap"))
xml_files = [os.path.join(xml_path, "Rootnet_FULL_NE_06J16h_DI.xml"),
             os.path.join(xml_path, "Rootnet_FULL_NE_06J16h_EQ.xml"),
             os.path.join(xml_path, "Rootnet_FULL_NE_06J16h_SV.xml"),
             os.path.join(xml_path, "Rootnet_FULL_NE_06J16h_TP.xml")]

# Read cim files and create new network.System object
res = cimpy.cim_import(xml_files, "cgmes_v2_4_15")
system_pyvolt = network.System()
base_apparent_power = 25  # MW
system_pyvolt.load_cim_data(res['topology'], base_apparent_power)

# Execute power flow analysis
results_pf, num_iter_cim = nv_powerflow.solve(system_pyvolt)

# Print powerflow node voltages
print("Pyvolt powerflow node voltages: ")
print("="*50)
for node in results_pf.nodes:
    print(f"{node.topology_node.uuid}\t=\t{node.voltage*1000:<6.8f}\t\t\t")
print("\n")

# Print powerflow branch power
print("Pyvolt powerflow branchpower (complex power flow at branch, measured at initial node): ")
print("="*50)
for branch in results_pf.branches:
    print(f"{branch.topology_branch.uuid}\t=\t{branch.power*1000:<6.8f}\t\t\t")
print("\n")


# --- State Estimation ---
""" Write here the percent uncertainties of the measurements"""
V_unc = 0
I_unc = 0
Sinj_unc = 0
S_unc = 0
Pmu_mag_unc = 1
Pmu_phase_unc = 2

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
state_estimation_results, covariance_nv = nv_state_estimator.DsseCall(system_pyvolt, measurements_set)

print("\n")

# Print state estimation node voltages
print("Pyvolt state estimation node voltages: ")
print("="*50)
for node_se in state_estimation_results.nodes:
    print(f"{node_se.topology_node.uuid}\t=\t{node_se.voltage*1000:<6.8f}\t\t\t")
print("\n")

# To obtain the Covariance matrix of estimated node voltages
print(covariance_nv)

# Print state estimation branch power
print("Pyvolt state estimation branchpower (complex power flow at branch, measured at final node): ")
print("="*50)    
for branch_se in state_estimation_results.branches:
    print(f"{branch_se.topology_branch.uuid}\t=\t{branch_se.power2*1000:<6.8f}\t\t\t")
