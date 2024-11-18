import pandas as pd

# Load the CSV file
file_path = '/home/bya/github/pyvolt/examples/test/logs/test.csv'
df = pd.read_csv(file_path)

# Check for empty columns
empty_columns = df.isnull().any()

# Print the headers that have empty values
empty_headers = empty_columns[empty_columns].index.tolist()

if empty_headers:
    print("The following headers have empty values:", empty_headers)
else:
    print("All headers have values.")