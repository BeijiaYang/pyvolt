import os
import cimpy
import numpy as np
import math
import logging
from scipy.stats import norm

from pyvolt import network
from pyvolt import nv_powerflow
from pyvolt import nv_state_estimator
from pyvolt import measurement
from pyvolt import results
import CovariancesCreation 

logging.basicConfig(filename='test_getCovPQI.log', level=logging.INFO, filemode='w')
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


# Repeated measurement creation and State Estimation experiments
iteration_num, iter = 1, 1
state_estimation_results_set = []
covariance_nv_set = []
covariance_pq_set = []
covariance_i_set  = []

while iter > 0:
    
    # Create measurements data structures
    """use all node voltages as measures"""
    measurements_set = measurement.MeasurementSet()
    for node in results_pf.nodes[-1:]:
        mean = np.absolute(node.voltage_pu)
        upper = mean*1.03
        lower = mean*0.99
        measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Vpmu_mag,
                                            mean, (upper - lower)/math.sqrt(12),
                                            [lower, upper])
    for node in results_pf.nodes[-1:]:
        mean = np.angle(node.voltage_pu)
        upper = mean
        lower = mean
        measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Vpmu_phase,
                                            mean, (upper - lower)/math.sqrt(12),
                                            [lower, upper])
    for node in results_pf.nodes[:]:
        mean = node.power_pu.real
        upper = mean*1.05
        lower = mean*0.9
        measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Sinj_real,
                                            mean, (upper - lower)/math.sqrt(12),
                                            [lower, upper])
    for node in results_pf.nodes[:]:
        mean = node.power_pu.imag
        upper = mean*1.03
        lower = mean*0.92
        measurements_set.create_measurement(node.topology_node, measurement.ElemType.Node, measurement.MeasType.Sinj_imag,
                                            mean, (upper - lower)/math.sqrt(12),
                                            [lower, upper])
    measurements_set.meas_creation(dist="uniform", type="band")

    # Perform state estimation
    state_estimation_results, covariance_nv = nv_state_estimator.DsseCall(system_pyvolt, measurements_set)

    print(f"\nIteration {iter}")
    print("="*70)
    print("\n")

    # Print state estimation node voltages
    print("Pyvolt state estimation node voltages: ")
    print("="*50)
    for node_se in state_estimation_results.nodes:
        print(f"{node_se.topology_node.uuid}\t=\t{node_se.voltage*1000:<6.8f}\t\t\t")
    print("\n")

    # To obtain the Covariance matrix of estimated node voltages
    print(covariance_nv)
    print(np.size(covariance_nv))

    # Print state estimation branch power
    print("Pyvolt state estimation branchpower (complex power flow at branch, measured at intial node): ")
    print("="*50)    
    for branch_se in state_estimation_results.branches:
        print(f"{branch_se.topology_branch.uuid}\t=\t{branch_se.power*1000:<6.8f}\t\t\t")
    print("\n")
        
    # Print state estimation branch current
    print("Pyvolt state estimation branchcurrent: ")
    print("="*50)    
    for branch_se in state_estimation_results.branches:
        print(f"{branch_se.topology_branch.uuid}\t=\t{branch_se.current*1000:<6.8f}\t\t\t")    
    print("\n")
    
    # Scale the branch power covariance matrix by the scaling factor
    scaling_factor = 1
    covariance_pq = CovariancesCreation.get_covariance_pq(state_estimation_results, covariance_nv)
    covariance_i  = CovariancesCreation.get_covariance_i (state_estimation_results, covariance_nv)
    for branch_id, cov_matrix_pq in covariance_pq.items():
        scaled_cov_matrix_pq = cov_matrix_pq * scaling_factor
        covariance_pq[branch_id] = scaled_cov_matrix_pq
    for branch_id, cov_matrix_i in covariance_i.items():
        scaled_cov_matrix_i = cov_matrix_i * scaling_factor
        covariance_i[branch_id] = scaled_cov_matrix_i
        
    print(covariance_pq)
    print(covariance_i)
    
    state_estimation_results_set.append(state_estimation_results)
    covariance_nv_set.append(covariance_nv)
    covariance_pq_set.append(covariance_pq)
    covariance_i_set .append(covariance_i)
    
    iter = iter - 1


# Define the violation thresholds (here manually setup as percentage larger than the first experiment)
violation_threshold_p = [branch.power.real*1.2 for branch in state_estimation_results_set[0].branches]
violation_threshold_q = [branch.power.imag*1.2 for branch in state_estimation_results_set[0].branches]
violation_threshold_ire = [branch.current.real*1.4 for branch in state_estimation_results_set[0].branches]
violation_threshold_iimag = [branch.current.imag*1.4 for branch in state_estimation_results_set[0].branches]

# Initialize the experiment data structure
probabilities = []
branch_num = len(state_estimation_results_set[0].branches)
p_set = np.zeros((iteration_num,branch_num))
q_set = np.zeros((iteration_num,branch_num))
cov_p_set = np.zeros((iteration_num,branch_num))
cov_q_set = np.zeros((iteration_num,branch_num))
ire_set = np.zeros((iteration_num,branch_num))
iimag_set = np.zeros((iteration_num,branch_num))
cov_ire_set = np.zeros((iteration_num,branch_num))
cov_iimag_set = np.zeros((iteration_num,branch_num))

# Construction of experiment data structure
for row, (res, cov_pq, cov_i) in enumerate(zip(state_estimation_results_set, covariance_pq_set, covariance_i_set)):
    for column, branch in enumerate(res.branches):

        # Store the power values for real and imaginary power (p and q)
        p_set[row, column] = branch.power.real
        q_set[row, column] = branch.power.imag
        
        ire_set[row, column] = branch.current.real
        iimag_set[row, column] = branch.current.imag
        
        
        # Store the corresponding covariance values for real and imaginary power
        cov_p_set[row, column] = cov_pq[branch.topology_branch.uuid][0, 0]
        cov_q_set[row, column] = cov_pq[branch.topology_branch.uuid][1, 1]
        
        cov_ire_set[row, column] = cov_i[branch.topology_branch.uuid][0, 0]
        cov_iimag_set[row, column] = cov_i[branch.topology_branch.uuid][1, 1]
        
        
# Loop through each branch (column) and each experiment (rows)
for column in range(p_set.shape[1]):     # Loop through branches
    for row in range(p_set.shape[0]):    # Loop through experiments
        
        prob_p = 1 - norm.cdf(np.abs(violation_threshold_p[column]), loc=np.abs(p_set[row, column]), scale=math.sqrt(cov_p_set[row, column]))
        prob_q = 1 - norm.cdf(np.abs(violation_threshold_q[column]), loc=np.abs(q_set[row, column]), scale=math.sqrt(cov_q_set[row, column]))
        prob_ire = 1 - norm.cdf(np.abs(violation_threshold_ire[column]), loc=np.abs(ire_set[row, column]), scale=math.sqrt(cov_ire_set[row, column]))
        prob_iimag = 1 - norm.cdf(np.abs(violation_threshold_iimag[column]), loc=np.abs(iimag_set[row, column]), scale=math.sqrt(cov_iimag_set[row, column]))

        probabilities.append((prob_p, prob_q, prob_ire, prob_iimag))

# Print the results for each branch and its corresponding probability
print("\n")
for branch, prob in zip(state_estimation_results_set[0].branches, probabilities):
    print(f"{branch.topology_branch.uuid}: Probability of violation (p, q, ireal, iimaginary): ({prob[0]:.4f}, {prob[1]:.4f} , {prob[2]:.4f}, {prob[3]:.4f})")
