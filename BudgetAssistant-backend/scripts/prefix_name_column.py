"""
Script to prefix every value in column 'Naam tegenpartij bevat' with a given prefix (default 'file2 ').
Usage:
    python prefix_name_column.py input.csv output.csv [--prefix PREFIX]
"""
import csv
import argparse

def main():
    parser = argparse.ArgumentParser(description="Prefix values in a specific CSV column.")
    parser.add_argument('--input', help='Path to input CSV file', default='C:/Users/daanv/Git/BudgetAssistant/BudgetAssistant-backend/pybackend/tests/resources/belfius-synthetic-data_processed2.csv')
    parser.add_argument('--output', help='Path to output CSV file', default='C:/Users/daanv/Git/BudgetAssistant/BudgetAssistant-backend/pybackend/tests/resources/belfius-synthetic-data_processed2-fixed.csv')
    parser.add_argument('--prefix', default='file2 ', help="Prefix string to add (default: 'file2 ')")
    args = parser.parse_args()

    with open(args.input, newline='', encoding='utf-8') as infile, \
         open(args.output, 'w', newline='', encoding='utf-8') as outfile:
        non_empty_lines = [line for line in infile if line.strip()]
        reader = csv.DictReader(non_empty_lines, delimiter=';')
        fieldnames = reader.fieldnames
        if not fieldnames or 'Naam tegenpartij bevat' not in fieldnames:
            raise ValueError("Column 'Naam tegenpartij bevat' not found in input file")
        writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
        writer.writeheader()

        for row in reader:
            row['Naam tegenpartij bevat'] = args.prefix + row['Naam tegenpartij bevat']
            writer.writerow(row)

if __name__ == '__main__':
    main()
