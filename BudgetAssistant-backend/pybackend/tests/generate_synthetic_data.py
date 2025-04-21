import csv
import importlib.resources as pkg_resources
with pkg_resources.open_text('pybackend.tests.resources',
                             "belfius-synthetic-data.csv",
                             encoding='utf-8') as file:

    csv.DictReader()

