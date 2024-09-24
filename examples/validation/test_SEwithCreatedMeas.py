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

# # Read CSV result file and store it in a results.Results object
# csv_file = os.path.realpath(os.path.join(this_file_folder,
#                                                       "..",
#                                                       "sample_data",
#                                                       "CIGRE-MV-NoTap",
#                                                       "CIGRE-MV-NoTap.csv"))

# powerflow_results = results.Results(system_pyvolt)
# powerflow_results.read_data(csv_file)

# Execute power flow analysis
results_pf, num_iter = nv_powerflow.solve(system_pyvolt)

# --- State Estimation with Ideal Measurements ---
""" Write here the percent uncertainties of the measurements"""
V_unc = 4
I_unc = 0
Sinj_unc = 2
Sinj_unc_wrong = 20
S_unc = 0
Pmu_mag_unc_1 = 0.8
Pmu_mag_unc_2 = 0.3
Pmu_phase_unc_1 = 0.1
Pmu_phase_unc_2 = 0.05

# ***********************************************
# ***State estimation with created measurements**
# ***********************************************
measurements_set = measurement.MeasurementSet()
for node in results_pf.nodes[ : len(results_pf.nodes)//4]:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Vpmu_mag,
                                        np.absolute(node.voltage_pu), Pmu_mag_unc_1)
for node in results_pf.nodes[ : len(results_pf.nodes)//4]:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Vpmu_phase,
                                        np.angle(node.voltage_pu), Pmu_phase_unc_1)
for node in results_pf.nodes[len(results_pf.nodes)//4 : len(results_pf.nodes)//2]:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Vpmu_mag,
                                        np.absolute(node.voltage_pu), Pmu_mag_unc_2)
for node in results_pf.nodes[len(results_pf.nodes)//4 : len(results_pf.nodes)//2]:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Vpmu_phase,
                                        np.angle(node.voltage_pu), Pmu_phase_unc_2)
for node in results_pf.nodes[len(results_pf.nodes)//2 : -1]:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.V_mag,
                                        np.absolute(node.voltage_pu) , V_unc)
for node in results_pf.nodes[ : -1]:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Sinj_real,
                                        node.power_pu.real , Sinj_unc)
for node in results_pf.nodes[ : -1]:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Sinj_imag,
                                        node.power_pu.imag , Sinj_unc)
for node in results_pf.nodes[-1 : ]:
    measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Sinj_imag,
                                        node.power_pu.imag , Sinj_unc_wrong)
measurements_set.meas_creation()

# print(measurements_set.getMeasValues())
# print(measurements_set.getWeightsMatrix())

# Perform state estimation
state_estimation_results = nv_state_estimator.DsseCall(system_pyvolt, measurements_set)

# Print node voltages
print("\n***State Estimation Results***\n")
print("Node ||"
      "State_estimation_results.voltages (V) ||  "
      "Assumed true voltages (V) || Mag. RER (%) || TVE rate (%)")
print("="*120)
for node_se, node_pf in zip(state_estimation_results.nodes, results_pf.nodes):
    mag_err = abs(abs(node_se.voltage) - abs(node_pf.voltage))
    mag_errR = mag_err / abs(node_pf.voltage)
    tve = np.absolute(node_se.voltage - node_pf.voltage)
    tveR = tve / abs(node_pf.voltage)
    print(f"{node_se.topology_node.uuid} "
          f"\t {node_se.voltage*1000:<6.6f} "
          f"\t\t {node_pf.voltage*1000:<6.6f} "
          f"\t {mag_errR * 100:<6.4f} "
          f"\t {tveR * 100:<6.4f}")

print("\n***Bad Data Detection***\n")
print("Node ||"
      " \tMeasured Values (V)\t||   "
      "Measurement type || Mag. RER (%) || TVE rate (%) || Notation")
print("="*120)
# Reformat the measurements for comparison with SE results
# Bad data detection based on error rate compared with SE results
# #SCADA V measurements
vidx = measurements_set.getIndexOfMeasurements(type=measurement.MeasType.V_mag)
if len(vidx) != 0:
    meas = measurements_set.measurements
    for i in vidx:
        for node_se in state_estimation_results.nodes:
            meas_value_mag = meas[i].meas_value * meas[i].element.baseVoltage
            if node_se.topology_node.uuid == meas[i].element.uuid:
                # magnitude error rate
                mag_err = abs(meas_value_mag - abs(node_se.voltage))
                mag_errR = mag_err / abs(node_se.voltage)
                # notation
                # Alarm when mag_errR > measurement standard deviation + SE error
                # here:SCADA uncertainty 5%, SE 1%
                if mag_errR > 5/300 + 0.01:
                    flag = "Bad Data!"
                else:
                    flag = " "
                print(f"{meas[i].element.uuid} "
                    f"\t\t{meas_value_mag*1000:<6.6f}"
                    f"\t\t\t{meas[i].meas_type}"
                    f"\t {mag_errR *100:<.4f}"                   
                    f" \t\t\t{flag}")
        
# #PMU mag phase measurements
# Reformat phasor measurements into real+jimag form
vridx = measurements_set.getIndexOfMeasurements(type=measurement.MeasType.Vpmu_mag)
if len(vridx) != 0:
    meas = measurements_set.measurements
    for i in vridx:
        # to find the corresponding phase measurement
        for ms in measurements_set.measurements:
            if ms.element.uuid == meas[i].element.uuid and ms.meas_type == measurement.MeasType.Vpmu_phase:
                meas_value_rect = meas[i].meas_value * meas[i].element.baseVoltage *  np.exp(1j * ms.meas_value) 
                for node_se in state_estimation_results.nodes:  
                    if node_se.topology_node.uuid == meas[i].element.uuid:
                        # TVE rate
                        tve = abs(node_se.voltage - meas_value_rect)
                        tveR = tve / abs(node_se.voltage)
                        # notation
                        # Alarm when tveR > measurement std_dev + 1%
                        if tveR > 1/300 + 0.01:
                            flag = "Bad Data!"
                        else:
                            flag = " "
        
                print(f"{meas[i].element.uuid}"
                      f"\t\t{meas_value_rect * 1000:<6.6f}"
                      f" \tPMU measurement"
                      f" \t"
                      f"\t{tveR *100:<.4f}"
                      f" \t\t\t{flag}")
        