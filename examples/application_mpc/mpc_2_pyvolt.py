import numpy as np
from pyvolt.network import Node, Branch, System, BusType
from pyvolt import nv_powerflow

def parse_case_topology(file_path):
    """
    Parses the MATPOWER case file into a Python dictionary for PyVolt mapping.
    :param file_path: Path to the MATPOWER .m file.
    :return: matpower_data dictionary.
    """
    matpower_data = {"buses": [], "branches": [], "generators": []}

    with open(file_path, 'r') as file:
        lines = file.readlines()

    section = None
    for line in lines:
        line = line.strip()
        if not line or line.startswith('%'):  # Skip comments and empty lines
            continue

        # Detect section start
        if line.startswith("mpc.bus = ["):
            section = "buses"
            continue
        elif line.startswith("mpc.branch = ["):
            section = "branches"
            continue
        elif line.startswith("mpc.gen = ["):
            section = "generators"
            continue
        elif line.startswith("];"):  # Section end
            section = None
            continue

        # Parse data
        if section == "buses":
            parts = list(map(float, line.replace(';', '').split()))
            matpower_data["buses"].append({
                "id": int(parts[0]),
                "type": int(parts[1]),
                "p_load": parts[2],
                "q_load": parts[3],
                "G_shunt": parts[4],
                "B_shunt": parts[5],
                "area": parts[6],
                "v_magnitude_pu": parts[7],
                "v_angle": parts[8],
                "baseVoltage(kV)": parts[9],
                "zone":parts[10],
                "Vmax": parts[11],
                "Vmin": parts[12],
            })
        elif section == "branches":
            parts = list(map(float, line.replace(';', '').split()))
            matpower_data["branches"].append({
                "from_bus": int(parts[0]),
                "to_bus": int(parts[1]),
                "r_pu": parts[2],
                "x_pu": parts[3],
                "b_pu": parts[4],
                "rateA": parts[5],
                "status": int(parts[10]),
            })
        elif section == "generators":
            parts = list(map(float, line.replace(';', '').split()))
            matpower_data["generators"].append({
                "bus": int(parts[0]),
                "p_generation": parts[1],
                "q_generation": parts[2],
                "q_max": parts[3],
                "q_min": parts[4],
                "v_setpoint": parts[5],
                "p_max": parts[8],
                "p_min": parts[9],
            })

    return matpower_data

def mpc_to_pyvolt(matpower_data):
    """
    Map MATPOWER data to PyVolt's System representation.
    :param matpower_data: Parsed MATPOWER data dictionary.
    :return: PyVolt System object.
    """
    system = System()

    # Add Nodes
    for idx, bus in enumerate(matpower_data["buses"]):
        node_type = BusType["PQ"]
        if bus["type"] == 1:
            node_type = BusType["SLACK"]
        elif bus["type"] == 2:
            node_type = BusType["PV"]

        node = Node(
            uuid=f"N{bus['id']}",
            name=f"{bus['id']}",
            base_voltage=bus["baseVoltage(kV)"], 
            base_apparent_power=100, 
            v_mag=bus["v_magnitude_pu"],
            v_phase=bus["v_angle"],
            p=bus["p_load"],
            q=bus["q_load"],
            index=idx
        )
        node.type = node_type
        system.nodes.append(node)

    # Add Branches
    for branch in matpower_data["branches"]:
        start_node = system.get_node_by_index(branch["from_bus"] - 1)
        end_node = system.get_node_by_index(branch["to_bus"] - 1)

        branch_obj = Branch(
            uuid=f"{branch['from_bus']}-{branch['to_bus']}",
            r=branch["r_pu"]*4,
            x=branch["x_pu"]*4,
            start_node=start_node,
            end_node=end_node,
            base_apparent_power=100,
            base_voltage=20,
        )
        system.branches.append(branch_obj)
        
    system.Ymatrix_calc()

    return system





if __name__ =="__main__":
    
    # Parse the matpower data
    file_path = 'case_topo\case_topology.m'  
    matpower_data = parse_case_topology(file_path)

    # Convert to Pyvolt network
    system_pyvolt = mpc_to_pyvolt(matpower_data)


    # Execute power flow analysis
    results_pf, num_iter = nv_powerflow.solve(system_pyvolt)

    # Print node voltages
    print("\n---Powerflow converged in " + str(num_iter) + " iterations.---\n")
    print("Results: \n")
    voltages = []
    for node in results_pf.nodes:
        print('{} = {} \n'.format(node.topology_node.uuid, node.current))
        #print('{}={} \n'.format(node.topology_node.uuid, node.voltage))
        # voltages.append(node.voltage_pu)
