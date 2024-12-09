import numpy as np
import matplotlib.pyplot as plt

def visual_branch_current(state_estimation_results, covariance_i, violation_threshold_i):
    branch_IDs = []
    branch_currents_mag = []
    covariances = []
    std_devs = []
    thresholds = []
    for index, branch in enumerate(state_estimation_results.branches):
        branch_IDs.append(branch.topology_branch.uuid)
        branch_currents_mag.append(np.abs(branch.current))
        covariances.append(covariance_i[branch.topology_branch.uuid][0,0])
        std_devs.append(np.sqrt(covariances[-1]))
        thresholds.append(violation_threshold_i[index])
        
    # Ensure consistency in data dimensions
    if not (len(branch_IDs) == len(branch_currents_mag) == len(std_devs)):
        raise ValueError("Mismatch in dimensions of branch data!")
    
    # Plot
    plt.figure(figsize=(10, 6))
    plt.bar(branch_IDs, branch_currents_mag, color='skyblue', label='Branch Current')
    plt.errorbar(branch_IDs, branch_currents_mag, yerr=3 * np.array(std_devs), fmt='.', 
                 color='black', ecolor='grey', elinewidth=2, capsize=5, label='Uncertainty')
    # Add individual threshold lines
    for i, (x, threshold) in enumerate(zip(branch_IDs, thresholds)):
        plt.hlines(y=thresholds[i], xmin=i - 0.4, xmax=i + 0.4, colors='orange', linestyles='dashed', label='Threshold' if i == 0 else None)
        
    # Labeling
    plt.xlabel('Branch ID')
    plt.ylabel('Branch Current in kA')
    plt.xticks(branch_IDs)  # Ensure all branch IDs are shown
    plt.legend(bbox_to_anchor=(0.05, 0))
    plt.grid(axis='y', linestyle='--', alpha=0.7)

    # Show plot
    plt.tight_layout()
    plt.show()
