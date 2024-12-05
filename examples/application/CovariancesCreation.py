import numpy as np

def get_covariance_pq(results, covariance_nv):
    """
    Compute the covariance matrix of branch power flows (P, Q) based on node voltage estimates.

    Parameters:
    results (pyvolt.results.PowerFlowResults): Power flow or state estimation results containing node voltages.
    covariance_nv (np.ndarray): Covariance matrix of node voltage estimates.

    Returns:
    branch_power_covariances (dict): Dictionary with branch UUIDs as keys and covariance matrices as values.
    """
    branch_power_covariances = {}
    
    for branch in results.branches:
        from_node = branch.topology_branch.start_node
        to_node   = branch.topology_branch.end_node
        
        v_from = from_node.voltage_pu
        v_to   = to_node.voltage_pu
        theta_from = np.angle(v_from)
        theta_to   = np.angle(v_to)
        v_mag_from = np.abs(v_from)
        v_mag_to   = np.abs(v_to)
        
        y_line = branch.topology_branch.y_pu
        g, b = y_line.real, y_line.imag
                
        # Jacobian of branch power flows (P, Q) w.r.t. voltage magnitudes and angles
        dp_dv_from = 2 * v_mag_from * g - v_mag_to * (g * np.cos(theta_from - theta_to) + b * np.sin(theta_from - theta_to))
        dp_dv_to = -v_mag_from * (g * np.cos(theta_from - theta_to) + b * np.sin(theta_from - theta_to))
        dp_dtheta_from = v_mag_from * v_mag_to * (g * np.sin(theta_from - theta_to) - b * np.cos(theta_from - theta_to))
        dp_dtheta_to = -dp_dtheta_from

        dq_dv_from = -2 * v_mag_from * b - v_mag_to * (g * np.sin(theta_from - theta_to) - b * np.cos(theta_from - theta_to))
        dq_dv_to = -v_mag_from * (g * np.sin(theta_from - theta_to) - b * np.cos(theta_from - theta_to))
        dq_dtheta_from = -v_mag_from * v_mag_to * (g * np.cos(theta_from - theta_to) + b * np.sin(theta_from - theta_to))
        dq_dtheta_to = -dq_dtheta_from

        # Assemble Jacobian
        num_nodes = len(results.nodes)
        jacobian = np.zeros((2, 2 * num_nodes))  # 2 rows for [P, Q], 2*num_nodes columns for [|V|, θ]
        from_idx = from_node.index
        to_idx = to_node.index

        jacobian[0, from_idx] = dp_dv_from
        jacobian[0, to_idx] = dp_dv_to
        jacobian[0, num_nodes + from_idx] = dp_dtheta_from
        jacobian[0, num_nodes + to_idx] = dp_dtheta_to

        jacobian[1, from_idx] = dq_dv_from
        jacobian[1, to_idx] = dq_dv_to
        jacobian[1, num_nodes + from_idx] = dq_dtheta_from
        jacobian[1, num_nodes + to_idx] = dq_dtheta_to

        # Compute covariance for this branch
        cov_pq = jacobian @ covariance_nv @ jacobian.T
        branch_power_covariances[branch.topology_branch.uuid] = cov_pq
        
           
    return branch_power_covariances  

def get_covariance_i_rec(results, covariance_nv):
    """
    Compute the covariance matrix of branch current based on node voltage estimates.
    The branch current is in rectangular form: I_re, I_imag

    Parameters:
    results (pyvolt.results.PowerFlowResults): Power flow or state estimation results containing node voltages.
    covariance_nv (np.ndarray): Covariance matrix of node voltage estimates.

    Returns:
    branch_current_covariances (dict): Dictionary with branch UUIDs as keys and covariance matrices as values.
    """
    branch_current_covariances = {}

    for branch in results.branches:
        from_node = branch.topology_branch.start_node
        to_node = branch.topology_branch.end_node
        
        v_from = from_node.voltage_pu
        v_to = to_node.voltage_pu
        theta_from = np.angle(v_from)
        theta_to = np.angle(v_to)
        v_mag_from = np.abs(v_from)
        v_mag_to = np.abs(v_to)
        
        y_line = branch.topology_branch.y_pu
        g, b = y_line.real, y_line.imag
        
       
        # Jacobian of current w.r.t. voltage magnitudes and angles
        num_nodes = len(results.nodes)
        jacobian = np.zeros((2, 2 * num_nodes))  # 2 rows for current (real and imaginary), 2*num_nodes columns for [|V|, θ]
        
        from_idx = from_node.index
        to_idx = to_node.index
        
         # Real part (Ir)
        jacobian[0, from_idx] = g
        jacobian[0, to_idx] = -g
        jacobian[0, num_nodes + from_idx] = -b * v_mag_from
        jacobian[0, num_nodes + to_idx] = b * v_mag_to

        # Imaginary part (Ii)
        jacobian[1, from_idx] = b
        jacobian[1, to_idx] = -b
        jacobian[1, num_nodes + from_idx] = g * v_mag_from
        jacobian[1, num_nodes + to_idx] = -g * v_mag_to

        # Compute the covariance matrix for the branch current
        cov_current = jacobian @ covariance_nv @ jacobian.T
        branch_current_covariances[branch.topology_branch.uuid] = cov_current
    
    return branch_current_covariances

def get_covariance_i(results, covariance_nv):
    """
    Compute the covariance matrix of branch current in polar form: I, theta.

    Parameters:
    results (pyvolt.results.PowerFlowResults): Power flow or state estimation results containing node voltages.
    covariance_nv (np.ndarray): Covariance matrix of node voltage estimates.

    Returns:
    branch_current_covariances_polar (dict): Dictionary with branch UUIDs as keys and polar covariance matrices as values.
    """
    branch_current_covariances_polar = {}
    branch_current_covariances_rect = get_covariance_i_rec(results, covariance_nv)
    
    for branch_uuid, cov_rect in branch_current_covariances_rect.items():
        # Extract real and imaginary covariance components
        I_r_var = cov_rect[0, 0]
        I_i_var = cov_rect[1, 1]
        I_r_I_i_cov = cov_rect[0, 1]
        
        # Current in rectangular coordinates
        I_r = cov_rect[0, 0]  # Mean real part (if needed for calculation)
        I_i = cov_rect[1, 1]  # Mean imaginary part (if needed for calculation)
        
        # Jacobian for polar conversion
        mag = np.sqrt(I_r**2 + I_i**2)
        J_polar = np.array([
            [I_r / mag, I_i / mag],
            [-I_i / (mag**2), I_r / (mag**2)]
        ])
        
        # Covariance in polar form
        cov_polar = J_polar @ cov_rect @ J_polar.T
        branch_current_covariances_polar[branch_uuid] = cov_polar
    
    return branch_current_covariances_polar
