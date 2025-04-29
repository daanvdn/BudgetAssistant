# Database Management Commands

## Truncate Tables Command

The `truncate_tables` command allows you to clear all data from the application's database tables while preserving the database structure and user accounts.

### Usage

#### Direct Command Usage

You can run the command directly using Django's management command interface:

```bash
python manage.py truncate_tables
```

#### Docker Usage

When running the application with Docker, you can set the `TRUNCATE_TABLES` environment variable to `true` to automatically truncate tables during container startup:

```bash
# Using docker-compose
TRUNCATE_TABLES=true docker-compose up django-backend

# Or set in .env file
TRUNCATE_TABLES=true
```

### What It Does

The command:

1. Temporarily disables foreign key constraints
2. Truncates all application tables in the correct order to avoid constraint violations
3. Preserves user accounts (CustomUser table is not truncated)
4. Re-enables foreign key constraints

### When to Use

This command is useful for:

- Development environments where you need a clean database
- Testing scenarios that require a fresh start
- Removing all transaction and category data while keeping user accounts

### Note

Be careful when using this command in production environments as it will delete all your data!

## Process CSV Command

The `process_csv` command allows you to process a CSV file by prepending the value of the "Transactienummer" column to specified columns.

### Usage

#### Direct Command Usage

You can run the command directly using Django's management command interface:

```bash
python manage.py process_csv <input_file> [--output-file <output_file>]
```

Where:
- `<input_file>` is the path to the CSV file to process
- `<output_file>` (optional) is the path where the processed CSV file will be saved. If not provided, the output will be saved to `<input_file>_processed.csv`

### What It Does

The command:

1. Reads a CSV file with semicolon (;) as the delimiter
2. For each row, prepends the value of the "Transactienummer" column to the following columns:
   - "Naam tegenpartij bevat"
   - "Transactie"
   - "Mededelingen"
3. Writes the modified data to a new CSV file

### When to Use

This command is useful for:

- Preprocessing CSV data before importing it into the system
- Adding transaction number references to make data more traceable
- Batch processing of transaction data files
