import logging
import os
import numpy as np
import json

from pyvolt import network, nv_powerflow, nv_state_estimator, measurement
import cimpy

logging.basicConfig(level=logging.INFO)

def run_state_estimation(xml_files: list) -> dict:
    """
    Given a list of CIM/RDF (XML) file paths, run the state estimation
    using pyvolt and return a dictionary with the estimated node voltages.
    """
    try:
        # Import CIM data using cimpy
        res = cimpy.cim_import(xml_files, "cgmes_v2_4_15")
        system = network.System()
        base_apparent_power = 2  # MW; adjust as necessary
        system.load_cim_data(res['topology'], base_apparent_power)

        # Execute power flow analysis
        results_pf, num_iter_cim = nv_powerflow.solve(system)

        # --- State Estimation ---
        Pmu_mag_unc = 0
        Pmu_phase_unc = 0

        measurements_set = measurement.MeasurementSet()
        for node in results_pf.nodes:
            measurements_set.create_measurement(
                node.topology_node,
                measurement.ElemType.Node,
                measurement.MeasType.Vpmu_mag,
                np.absolute(node.voltage_pu),
                Pmu_mag_unc
            )
        for node in results_pf.nodes:
            measurements_set.create_measurement(
                node.topology_node,
                measurement.ElemType.Node,
                measurement.MeasType.Vpmu_phase,
                np.angle(node.voltage_pu),
                Pmu_phase_unc
            )
        measurements_set.meas_creation()

        # Perform state estimation
        state_estimation_results = nv_state_estimator.DsseCall(system, measurements_set)

        results = {}
        for node in state_estimation_results.nodes:
            voltage = node.voltage
            if isinstance(voltage, complex):
                results[node.topology_node.uuid] = {
                    "real": float(voltage.real),
                    "imag": float(voltage.imag)
                }
            elif isinstance(voltage, dict):
                results[node.topology_node.uuid] = {
                    "real": float(voltage.get("real", 0)),
                    "imag": float(voltage.get("imag", 0))
                }
            else:
                try:
                    comp_voltage = complex(voltage)
                    results[node.topology_node.uuid] = {
                        "real": float(comp_voltage.real),
                        "imag": float(comp_voltage.imag)
                    }
                except Exception:
                    results[node.topology_node.uuid] = str(voltage)
        return results

    except Exception as e:
        logging.exception("State estimation failed")
        raise e
