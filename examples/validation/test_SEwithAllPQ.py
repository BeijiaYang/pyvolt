import os
import logging
import numpy as np
import matplotlib.pyplot as plt

import cimpy
from pyvolt import network
from pyvolt import nv_powerflow
from pyvolt import nv_state_estimator
from pyvolt import measurement
from pyvolt import results


logging.basicConfig(filename='test_nv_state_estimator.log', level=logging.INFO, filemode='w')

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
results_pf, num_iter = nv_powerflow.solve(system_pyvolt)

# --- State Estimation with Ideal Measurements ---
""" Write here the percent uncertainties of the measurements"""
""" Phase uncertainty is absolute uncertainty"""
Sinj_unc_mag = 0.8
Sinj_unc_phase = 0.1

# ***********************************************
# Insufficient measurements leads to SE "failure"
# ***********************************************
"""No related measurement for last node"""
measurements_set = measurement.MeasurementSet()
for node in results_pf.nodes[ : ]:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Sinj_real,
                                        node.power_pu.real, Sinj_unc_mag)
for node in results_pf.nodes[ : ]:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Sinj_imag,
                                        node.power_pu.imag, Sinj_unc_phase)
measurements_set.meas_creation()

# print(measurements_set.getMeasValues())
# print(measurements_set.getWeightsMatrix())

# Perform state estimation
state_estimation_results = nv_state_estimator.DsseCall(system_pyvolt, measurements_set)

# Print node voltages
print("Node ||"
      "State_estimation_results.voltages (V) ||  "
      "Assumed true voltages (V) || Mag. RER (%) || TVE rate (%) ||\t Notation")

print("="*150)

for node_se, node_pf in zip(state_estimation_results.nodes, results_pf.nodes):
    # magnitude error rate
    mag_err = abs(abs(node_se.voltage) - abs(node_pf.voltage))
    mag_errR = mag_err / abs(node_pf.voltage)
    # total vector error rate
    tve = abs(node_se.voltage - node_pf.voltage)
    tveR = tve / abs(node_pf.voltage)
    # notations
    if tveR > 1.0 / 100 and mag_errR > 1.0 / 100:
        flag = "SE failure!"
    else:
        flag = " "

    print(f"{node_se.topology_node.uuid} "
          f"\t {node_se.voltage*1000:<6.6f} "
          f"\t\t {node_pf.voltage*1000:<6.6f} "
          f"\t {mag_errR * 100:<6.4f} "
          f"\t {tveR * 100:<6.4f}" 
          f"\t {flag}")

