import json
import csv
import re

# Remove all the unexpected trailing commas in the package
def remove_trailing_commas(input_file, output_file):
    # Read the content of the input file
    with open(input_file, 'r') as file:
        content = file.read()

    # Use regex to find and remove trailing commas before closing brackets and braces
    # This pattern finds a comma followed by any amount of whitespace and then a closing bracket/brace
    cleaned_content = re.sub(r',\s*([\]}])', r'\1', content)

    # Write the cleaned content to the output file
    with open(output_file, 'w') as file:
        file.write(cleaned_content)

    print(f"Trailing commas removed and saved to {output_file}")


# Extract the package data adn store into a csv
def extract_pmu_data(input_txt_file, output_csv_file):
    # Read the PMU data from the .txt file
    with open(input_txt_file, 'r') as file:
        pmu_data = file.read()

    # Parse the PMU data as JSON
    pmu_data_json = json.loads(pmu_data)

    # Extract the timestamp
    timestamp = pmu_data_json['timestamp']

    # Extract magnitudes, phases, and channels from readings
    extracted_data = []
    for reading in pmu_data_json['readings']:
        channel = reading['channel']
        magnitude = reading['magnitude']
        phase = reading['phase']
        extracted_data.append({"channel": channel, "magnitude": magnitude, "phase": phase, "timestamp": timestamp})

    #  Write to CSV with padding
    with open(output_csv_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)

        column_widths = [8, 12, 10, 30]
        
        # Write the header row with padding
        headers = ["Channel", "Magnitude", "Phase", "Timestamp"]
        padded_headers = [header.ljust(width) for header, width in zip(headers, column_widths)]
        writer.writerow(padded_headers)
    
        # Write the data rows with padding
        for reading in pmu_data_json['readings']:
            channel = reading['channel']
            magnitude = reading['magnitude']
            phase = reading['phase']
            row = [channel, magnitude, phase, timestamp]
            # Apply padding to each field
            padded_row = [str(item).ljust(width) for item, width in zip(row, column_widths)]
            writer.writerow(padded_row)

    print(f"Data extracted and saved to {output_csv_file} with padding.")


if __name__ == "__main__":
    
    # Example usage
    input_file = "package_example.txt" 
    input_file_cleaned = "package_example_cleaned.txt"

    remove_trailing_commas(input_file, input_file_cleaned)
    
    # Example usage:
    input_file_cleaned = "package_example_cleaned.txt"
    output_file_csv = "pmu_measurements.csv"

    extract_pmu_data(input_file_cleaned, output_file_csv)
