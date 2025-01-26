from datetime import datetime

from django.test import TestCase

from pybackend.commons import RecurrenceType, RevenueExpensesQuery, TransactionPredicates, TransactionTypeEnum
from pybackend.models import BankAccount, Counterparty, CustomUser, Transaction


class TransactionPredicatesTests(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create(username='testuser', password='password')
        self.bank_account = BankAccount.objects.create(account_number='123456789')
        self.bank_account.users.add(self.user)
        self.start_date = datetime(2023, 1, 1)
        self.end_date = datetime(2023, 12, 31)

        self.counterparty1 = Counterparty.objects.create(name='counterparty1', account_number='123')
        self.counterparty2 = Counterparty.objects.create(name='counterparty2', account_number='456')

        self.transaction_revenue = Transaction.objects.create(
            transaction_id='1', bank_account=self.bank_account, booking_date=self.start_date,
            statement_number='1', counterparty=self.counterparty1, transaction_number='1',
            transaction='Test Transaction', currency_date=self.start_date, amount=100.0, currency='USD',
            bic='BIC', country_code='US', communications='Test', is_recurring=True
        )
        self.transaction_expense = Transaction.objects.create(
            transaction_id='2', bank_account=self.bank_account, booking_date=self.start_date,
            statement_number='2', counterparty=self.counterparty2, transaction_number='2',
            transaction='Test Transaction', currency_date=self.start_date, amount=-50.0, currency='USD',
            bic='BIC', country_code='US', communications='Test', is_recurring=False
        )

    def test_has_period_returns_correct_query(self):
        query = TransactionPredicates.has_period(self.start_date, self.end_date)
        transactions = Transaction.objects.filter(query)
        self.assertIn(self.transaction_revenue, transactions)
        self.assertIn(self.transaction_expense, transactions)

    def test_has_account_number_returns_correct_query(self):
        query = TransactionPredicates.has_account_number('123456789')
        transactions = Transaction.objects.filter(query)
        self.assertIn(self.transaction_revenue, transactions)
        self.assertIn(self.transaction_expense, transactions)

    def test_transaction_type_with_recurrence_revenue_recurrent(self):
        query = TransactionPredicates.transaction_type_with_recurrence(TransactionTypeEnum.REVENUE, RecurrenceType.RECURRENT, RecurrenceType.BOTH)
        transactions = Transaction.objects.filter(query)
        self.assertIn(self.transaction_revenue, transactions)
        self.assertNotIn(self.transaction_expense, transactions)

    def test_transaction_type_with_recurrence_expenses_non_recurrent(self):
        query = TransactionPredicates.transaction_type_with_recurrence(TransactionTypeEnum.EXPENSES, RecurrenceType.NON_RECURRENT, RecurrenceType.BOTH)
        transactions = Transaction.objects.filter(query)
        self.assertIn(self.transaction_expense, transactions)
        self.assertNotIn(self.transaction_revenue, transactions)

    def test_transaction_type_with_recurrence_both(self):
        query = TransactionPredicates.transaction_type_with_recurrence(TransactionTypeEnum.BOTH, RecurrenceType.BOTH, RecurrenceType.BOTH)
        transactions = Transaction.objects.filter(query)
        self.assertIn(self.transaction_revenue, transactions)
        self.assertIn(self.transaction_expense, transactions)

    def test_has_period_account_number_and_is_revenue(self):

        revenue_expenses_query = RevenueExpensesQuery(
            account_number= '123456789',
            transaction_type= TransactionTypeEnum.REVENUE,
            start= self.start_date,
            end= self.end_date,
            revenue_recurrence= RecurrenceType.RECURRENT,
            expenses_recurrence= RecurrenceType.BOTH,
            grouping=None

        )
        query = TransactionPredicates.has_period_account_number_and_is_revenue(revenue_expenses_query)
        transactions = Transaction.objects.filter(query)
        self.assertIn(self.transaction_revenue, transactions)
        self.assertNotIn(self.transaction_expense, transactions)

    def test_requires_manual_review_revenue(self):
        query = TransactionPredicates.requires_manual_review(self.bank_account, TransactionTypeEnum.REVENUE)
        transactions = Transaction.objects.filter(query)
        self.assertIn(self.transaction_revenue, transactions)
        self.assertNotIn(self.transaction_expense, transactions)

    def test_requires_manual_review_expenses(self):
        query = TransactionPredicates.requires_manual_review(self.bank_account, TransactionTypeEnum.EXPENSES)
        transactions = Transaction.objects.filter(query)
        self.assertIn(self.transaction_expense, transactions)
        self.assertNotIn(self.transaction_revenue, transactions)


