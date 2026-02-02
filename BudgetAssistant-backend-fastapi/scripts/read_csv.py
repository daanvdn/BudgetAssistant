import sys


def read_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read()
            print(f"File content (first 1000 characters):\n{content[:1000]}")

            # Count non-empty lines
            lines = content.split("\n")
            non_empty_lines = [line for line in lines if line.strip()]
            print(f"\nTotal lines: {len(lines)}")
            print(f"Non-empty lines: {len(non_empty_lines)}")

            # Print first non-empty line (likely the header)
            if non_empty_lines:
                print(f"\nFirst non-empty line (likely header):\n{non_empty_lines[0]}")

                # Check if semicolon is present in the first non-empty line
                if ";" in non_empty_lines[0]:
                    columns = non_empty_lines[0].split(";")
                    print(f"\nColumns (split by semicolon): {columns}")
                    print(f"Number of columns: {len(columns)}")
                else:
                    print("\nNo semicolons found in the header line.")

            # Print a few data lines if available
            if len(non_empty_lines) > 1:
                print("\nFirst few data lines:")
                for i, line in enumerate(non_empty_lines[1:6]):  # Print up to 5 data lines
                    print(f"Data line {i + 1}: {line}")

    except Exception as e:
        print(f"Error reading file: {str(e)}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python read_csv.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    read_file(file_path)
