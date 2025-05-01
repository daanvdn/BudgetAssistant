import csv
import os
import sys

def process_csv(input_file, output_file=None):
    """
    Process a CSV file to prepend the Transactienummer value to specified columns.

    Args:
        input_file (str): Path to the input CSV file
        output_file (str, optional): Path to the output CSV file. If not provided,
                                    defaults to input_file with _processed suffix.
    """
    if not output_file:
        # Create default output filename by adding _processed before the extension
        base, ext = os.path.splitext(input_file)
        output_file = f"{base}_processed{ext}"

    print(f'Processing CSV file: {input_file}')
    print(f'Output will be written to: {output_file}')

    # Columns to modify
    columns_to_modify = [
        'Naam tegenpartij bevat',
        'Transactie',
        'Mededelingen'
    ]

    try:
        # Read the file content to analyze it
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Count non-empty lines
        lines = content.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        print(f"Total lines: {len(lines)}")
        print(f"Non-empty lines: {len(non_empty_lines)}")

        if not non_empty_lines:
            print("Error: No data found in the CSV file")
            return

        # Get the header line
        header_line = non_empty_lines[0]

        # Check if semicolon is present in the header line
        if ';' in header_line:
            delimiter = ';'
        else:
            delimiter = ','

        print(f"Using delimiter: '{delimiter}'")

        # Get the column names
        fieldnames = header_line.split(delimiter)
        print(f"CSV columns found: {fieldnames}")

        # Verify that required columns exist
        if 'Transactienummer' not in fieldnames:
            print('Error: Transactienummer column not found in the CSV file')
            return

        for column in columns_to_modify:
            if column not in fieldnames:
                print(f'Error: {column} column not found in the CSV file')
                return

        # Process the data
        processed_data = []
        processed_data.append(header_line)  # Add header line

        # Process each data line
        for line in non_empty_lines[1:]:
            fields = line.split(delimiter)
            if len(fields) != len(fieldnames):
                print(f"Warning: Line has {len(fields)} fields, expected {len(fieldnames)}. Skipping.")
                continue

            # Create a dictionary for this row
            row = {fieldnames[i]: fields[i] for i in range(len(fieldnames))}

            # Get the transaction number
            transaction_number = row['Transactienummer']

            # Modify the specified columns
            for column in columns_to_modify:
                column_index = fieldnames.index(column)
                if fields[column_index]:  # Only modify if the column has a value
                    fields[column_index] = f"{transaction_number} {fields[column_index]}"

            # Add the modified line to processed data
            processed_data.append(delimiter.join(fields))

        # Write to the output CSV file
        with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
            outfile.write('\n'.join(processed_data))

        print('CSV processing completed successfully!')

    except Exception as e:
        print(f'Error processing CSV file: {str(e)}')

if __name__ == "__main__":
    # Check if input file is provided as command line argument
    if len(sys.argv) < 2:
        print("Usage: python process_csv.py <input_file> [output_file]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    process_csv(input_file, output_file)
