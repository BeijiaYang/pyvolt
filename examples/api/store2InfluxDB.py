import os
import json
from influxdb_client_3 import InfluxDBClient3, Point


def storeData(results, job_id):
    
    # InfluxDB configuration
    myToken = os.environ.get("INFLUXDB_TOKEN")
    myOrg = "RWTH Aachen University, Eon ERC"
    myHost = "https://eu-central-1-1.aws.cloud2.influxdata.com"
    myBucket = "test_simulation"
    test_typology = "test_grid"

    # Initialize the InfluxDB client
    client = InfluxDBClient3(host=myHost, token=myToken, org=myOrg)
        
    for node_id, voltage in results.items():
        if isinstance(voltage, complex):
            point = (
                Point(test_typology)
                .tag("Node_ID", node_id)
                .tag("job_id", job_id)
                .field("real", float(voltage.real))
                .field("imag", float(voltage.imag))
            )
        elif isinstance(voltage, dict):
            point = (
                Point(test_typology)
                .tag("Node_ID", node_id)
                .tag("job_id", job_id)
                .field("real", float(voltage.get("real", 0)))
                .field("imag", float(voltage.get("imag", 0)))
            )
        else:
            try:
                comp_voltage = complex(voltage)
                point = (
                    Point(test_typology)
                    .tag("Node_ID", node_id)
                    .tag("job_id", job_id)
                    .field("real", float(comp_voltage.real))
                    .field("imag", float(comp_voltage.imag))
            )
            except Exception:
                point = (
                    Point(test_typology)
                    .tag("Node_ID", node_id)
                    .tag("job_id", job_id)
                    .field("real", float(voltage.real))
                    .field("imag", float(voltage.imag))
            )
    
        client.write(database=myBucket, record=point)


