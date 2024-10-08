import re

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

# Example usage
input_file = 'package_example.txt'  # Replace with your actual input file
output_file = 'package_example_cleaned.txt'

remove_trailing_commas(input_file, output_file)