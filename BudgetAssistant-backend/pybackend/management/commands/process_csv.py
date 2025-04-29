from django.core.management.base import BaseCommand
import csv
import os

class Command(BaseCommand):
    help = 'Process CSV file to prepend Transactienummer to specified columns'

    def add_arguments(self, parser):
        parser.add_argument('input_file', type=str, help='Path to the input CSV file')
        parser.add_argument('--output-file', type=str, help='Path to the output CSV file (default: input_file with _processed suffix)')

    def handle(self, *args, **options):
        input_file = options['input_file']
        output_file = options.get('output_file')
        
        if not output_file:
            # Create default output filename by adding _processed before the extension
            base, ext = os.path.splitext(input_file)
            output_file = f"{base}_processed{ext}"
        
        self.stdout.write(self.style.SUCCESS(f'Processing CSV file: {input_file}'))
        self.stdout.write(self.style.SUCCESS(f'Output will be written to: {output_file}'))
        
        # Columns to modify
        columns_to_modify = [
            'Naam tegenpartij bevat',
            'Transactie',
            'Mededelingen'
        ]
        
        try:
            # Read the input CSV file
            with open(input_file, 'r', newline='', encoding='utf-8') as infile:
                reader = csv.DictReader(infile, delimiter=';')
                fieldnames = reader.fieldnames
                
                # Verify that required columns exist
                if 'Transactienummer' not in fieldnames:
                    self.stdout.write(self.style.ERROR('Error: Transactienummer column not found in the CSV file'))
                    return
                
                for column in columns_to_modify:
                    if column not in fieldnames:
                        self.stdout.write(self.style.ERROR(f'Error: {column} column not found in the CSV file'))
                        return
                
                # Write to the output CSV file
                with open(output_file, 'w', newline='', encoding='utf-8') as outfile:
                    writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=';')
                    writer.writeheader()
                    
                    # Process each row
                    for row in reader:
                        transaction_number = row['Transactienummer']
                        
                        # Modify the specified columns
                        for column in columns_to_modify:
                            if row[column]:  # Only modify if the column has a value
                                row[column] = f"{transaction_number} {row[column]}"
                        
                        # Write the modified row
                        writer.writerow(row)
            
            self.stdout.write(self.style.SUCCESS('CSV processing completed successfully!'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing CSV file: {str(e)}'))