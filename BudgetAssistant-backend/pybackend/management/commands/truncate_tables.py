from django.core.management.base import BaseCommand
from django.db import connection
from pybackend.models import (
    BankAccount, CustomUser, Transaction, Counterparty,
    CategoryTree, Category, BudgetTree, BudgetTreeNode, TreeNode
)

class Command(BaseCommand):
    help = 'Truncates all application tables while respecting foreign key constraints'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting database truncation...'))
        
        # Get cursor
        cursor = connection.cursor()
        
        # Temporarily disable foreign key constraints
        if connection.vendor == 'mysql':
            cursor.execute('SET FOREIGN_KEY_CHECKS=0;')
        elif connection.vendor == 'sqlite':
            cursor.execute('PRAGMA foreign_keys=OFF;')
        
        # Truncate tables in reverse order of dependencies
        self.truncate_model(TreeNode)
        self.truncate_model(BudgetTreeNode)
        self.truncate_model(BudgetTree)
        self.truncate_model(Category)
        self.truncate_model(CategoryTree)
        self.truncate_model(Transaction)
        self.truncate_model(Counterparty)
        # Don't truncate CustomUser to preserve login credentials
        # self.truncate_model(CustomUser)
        self.truncate_model(BankAccount)
        
        # Re-enable foreign key constraints
        if connection.vendor == 'mysql':
            cursor.execute('SET FOREIGN_KEY_CHECKS=1;')
        elif connection.vendor == 'sqlite':
            cursor.execute('PRAGMA foreign_keys=ON;')
        
        self.stdout.write(self.style.SUCCESS('Successfully truncated all tables!'))
    
    def truncate_model(self, model):
        model_name = model.__name__
        self.stdout.write(f'Truncating {model_name}...')
        model.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully truncated {model_name}!'))