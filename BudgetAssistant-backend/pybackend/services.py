# src/main/python/budget-assistant-backend-django/pybackend/services/user_service.py

import logging
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Union

from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from silk.profiling.profiler import silk_profile

from pybackend.analysis import BudgetTracker, BudgetTrackerResult, CategoryDetailsForPeriodHandler, \
    CategoryDetailsForPeriodHandlerResult, ExpensesAndRevenueForPeriod, \
    RevenueAndExpensesPerPeriodAndCategory, TransactionDistributionHandler
from pybackend.categorization import Categorizer
from pybackend.commons import RevenueExpensesQuery, TransactionInContextQuery, TransactionPredicates, TransactionQuery, \
    TransactionTypeEnum
from pybackend.dto import CategorizeTransactionsResponse, FailedOperationResponse, SuccessfulOperationResponse, \
    TransactionsPage
from pybackend.models import BankAccount, BudgetTree, Category, CustomUser, \
    Transaction
from pybackend.period import ResolvedStartEndDateShortcut, StartEndDateShortcut, StartEndDateShortcutResolver
from pybackend.rules import RuleSet, RuleSetWrapper
from pybackend.serializers import TransactionSerializer
from pybackend.transactions_parsing import ParseResult

logger = logging.getLogger(__name__)

class BankAccountsService:
    def get_or_create_bank_account(self, account_number: str, user: CustomUser) -> BankAccount:
        account_number = BankAccount.normalize_account_number(account_number)
        bank_account, created = BankAccount.objects.get_or_create(account_number=account_number)
        if created:
            bank_account.users.add(user)
        elif user not in bank_account.users.all():
            bank_account.users.add(user)
        return bank_account

    def find_distinct_by_users_contains(self, user: CustomUser):
        return BankAccount.objects.filter(users=user).distinct()

    def get_bank_account(self, account_number: str) -> BankAccount:
        try:
            return BankAccount.objects.get(account_number=account_number)
        except ObjectDoesNotExist as e:
            raise ValueError(f"Bank account with account number {account_number} does not exist")

    def save_alias(self, account_number: str, alias: str) -> None:
        bank_account = self.get_bank_account(account_number)
        bank_account.alias = alias
        bank_account.save()

class TransactionsService:
    def __init__(self):

        self.categorizer = Categorizer()

    @silk_profile(name='TransactionsService.page_transactions_to_manually_review')
    def page_transactions_to_manually_review(self, bank_account: str, page: int, size: int, sort_order: str,
                                             sort_property: str,
                                             transaction_type: TransactionTypeEnum) -> TransactionsPage:
        sort_order = sort_order.lower()
        if sort_order not in ['asc', 'desc']:
            raise ValueError(f"Invalid sort order: {sort_order}")
        prefix = "-" if sort_order == 'desc' else ""
        sort = f"{prefix}{sort_property}"
        bank_account_obj = BankAccount.objects.get(account_number=bank_account)

        # Create a base queryset with optimized joins
        transactions = Transaction.objects.select_related(
            'bank_account', 
            'counterparty', 
            'category'
        ).prefetch_related(
            'counterparty__users'
        ).filter(
            TransactionPredicates.requires_manual_review(bank_account_obj, transaction_type)
        ).order_by(sort)

        paginator = Paginator(transactions, size)
        page_obj = paginator.get_page(page)
        return TransactionsPage(content=page_obj.object_list, number=page_obj.number, size=size,
                                total_elements=paginator.count)

    def count_transactions_to_manually_review(self, bank_account: str) -> int:
        bank_account_obj = BankAccount.objects.get(account_number=bank_account)
        # For count operations, we don't need to select_related or prefetch_related
        # as we're only interested in the count, not the actual objects
        count = Transaction.objects.filter(TransactionPredicates.requires_manual_review(bank_account=bank_account_obj,
                                                             transaction_type=TransactionTypeEnum.BOTH)).count()
        return count
    def _get_bank_accounts_for_user(self, user: CustomUser) -> List[str]:
        # Use values_list to directly fetch only the account_number field
        # This is more efficient than fetching entire objects when we only need one field
        return list(BankAccount.objects.filter(users=user).values_list('account_number', flat=True))

    def page_transactions(self, query: Optional[TransactionQuery], page: int, size: int, sort_order: str,
                          sort_property: str, user:CustomUser) -> TransactionsPage:

        @silk_profile(name='TransactionsService.page_transactions._get_transactions_for_query')
        def _get_transactions_for_query(query, sort_order, sort_property, user):
            direction = sort_order.upper()
            if direction not in ['ASC', 'DESC']:
                raise ValueError(f"Invalid sort order: {direction}")
            sort = f"-{sort_property}" if direction == 'DESC' else sort_property
            bank_accounts_for_user = self._get_bank_accounts_for_user(user)
            q = TransactionPredicates.bank_account_number_in(bank_accounts_for_user)
            # Create a base queryset with optimized joins
            base_queryset = Transaction.objects.select_related(
                'bank_account',
                'counterparty',
                'category'
            ).prefetch_related(
                'counterparty__users'
            )
            if not query:
                transactions = base_queryset.filter(q).order_by(sort)
            else:
                predicate = TransactionPredicates.from_transaction_query(query)
                if predicate:
                    transactions = base_queryset.filter(predicate).order_by(sort)
                else:
                    transactions = base_queryset.all().order_by(sort)
            transactions = transactions.filter(q)
            return transactions

        transactions = _get_transactions_for_query(query, sort_order, sort_property, user)
        paginator = Paginator(transactions, size)
        page_obj = paginator.get_page(page)
        return TransactionsPage(content=page_obj.object_list, number=page_obj.number,
                                size=size,
                                total_elements=paginator.count)


    def page_transactions_in_context(self, query: Optional[TransactionInContextQuery], page: int, size: int,
                                     sort_order: str,
                                     sort_property: str) -> TransactionsPage:

        direction = sort_order.upper()
        sort = f"{direction}{sort_property}"

        # Create a base queryset with optimized joins
        base_queryset = Transaction.objects.select_related(
            'bank_account', 
            'counterparty', 
            'category'
        ).prefetch_related(
            'counterparty__users'
        )

        if not query:
            transactions = base_queryset.all().order_by(sort)
        else:
            predicate = TransactionPredicates.from_transaction_in_context_query(query)
            if predicate:
                transactions = base_queryset.filter(predicate).order_by(sort)
            else:
                transactions = base_queryset.all().order_by(sort)
        paginator = Paginator(transactions, size)
        page_obj = paginator.get_page(page)
        content = list(page_obj)  # Convert to list directly

        return TransactionsPage(content=content, number=page_obj.number, size=size,
                                total_elements=paginator.count)

    def save_transaction(self, transaction_json: Dict) -> Union[
        SuccessfulOperationResponse,
        FailedOperationResponse
    ]:
        try:
            id = transaction_json['transaction_id']
            transaction = Transaction.objects.get(transaction_id=id)
            counterparty = transaction_json.pop('counterparty', None)
            if counterparty and isinstance(counterparty, dict):
                transaction_json['counterparty_id']= counterparty['name']
            serializer = TransactionSerializer(transaction, data=transaction_json)
            if serializer.is_valid(raise_exception=False):
                # update the transaction with the new data
                serializer.save()
                return SuccessfulOperationResponse(message=f"Transaction with id '{id}' updated successfully")
            else:
                # convert serializer.errors to a string
                message = str(serializer.errors)
                return FailedOperationResponse(error=message, status_code=400)

        except ObjectDoesNotExist:
            return FailedOperationResponse(
                error=f"Transaction with id '{transaction_json['transaction_id']}' does not exist in db!", status_code=500)

    @transaction.atomic
    def upload_transactions(self, lines, user: CustomUser, upload_timestamp: datetime, transaction_parser, file_name) -> ParseResult:
        try:
            self.categorizer.load_rules(user)
            parse_result = transaction_parser.parse(lines, user)
            transactions = parse_result.transactions
            if not transactions or len(transactions) == 0:
                raise Exception(f"No transactions were parsed from file '{lines.name}'")

            # Set upload_timestamp for all transactions
            for transaction in transactions:
                transaction.upload_timestamp = upload_timestamp

            # Separate transactions that need categorization
            transactions_to_categorize = [t for t in transactions if not t.category]

            # Batch categorize transactions
            if transactions_to_categorize:
                categorized_transactions = self.categorizer.categorize_list(transactions_to_categorize, user)
                # Update the original transactions with the categorized ones
                for i, transaction in enumerate(transactions_to_categorize):
                    transaction.category = categorized_transactions[i].category
                    transaction.save()

            # Note: The transaction_parser.parse method now handles the creation and updating of transactions
            # in a more efficient way using bulk operations, so we don't need to do additional processing here.

            logger.info(f"Uploaded {parse_result.created} new transactions from file '{file_name}'. Ignored {parse_result.ignored} existing transactions.")

            return parse_result
        except Exception as e:
            traceback.print_exc()
            logger.error(str(e))
            raise Exception(f"Error when processing transactions file with name '{file_name}'. Exception: {str(e)}")

    def categorise_transactions(self, user: CustomUser) -> CategorizeTransactionsResponse:
        distinct_accounts = BankAccount.objects.filter(users=user).distinct()
        self.categorizer.load_rules(user)
        with_category = 0
        without_category = 0
        for bank_account in distinct_accounts:
            transactions = Transaction.objects.filter(bank_account=bank_account,
                                                      manually_assigned_category=False)
            categorized_transaction = self.categorizer.categorize(transactions, user)
            if categorized_transaction.has_category():
                with_category += 1
                categorized_transaction.save()
            else:
                without_category += 1

        return CategorizeTransactionsResponse(
            message=f"Categorized {with_category} transactions; {without_category} transactions have no category",
            with_category_count=with_category,
            without_category_count=without_category)

class BudgetTreeService:

    @transaction.atomic
    def find_or_create_budget(self, bank_account_number: str) -> JsonResponse:
        raise Exception("Not implemented. Moved all logic to views")

class RuleSetsService:

    @transaction.atomic
    def get_or_create_rule_set_wrapper(self, type, user: CustomUser, category_qualified_name: str) -> RuleSetWrapper:
        try:
            category = Category.objects.get(name=category_qualified_name, type=type)
            rule_set_wrapper = RuleSetWrapper.objects.find_by_type_and_category_and_user(type, user, category)
            if not rule_set_wrapper:
                rule_set_wrapper = RuleSetWrapper(category=category,
                                                  rule_set=RuleSet(condition='AND', rules=[], is_child=False, clazz='',
                                                                   type=type))
                rule_set_wrapper.save()
                rule_set_wrapper.users.add(user)
            return rule_set_wrapper
        except ObjectDoesNotExist:
            raise ValueError(f"Category with name {category_qualified_name} and type {type} does not exist")
        except Exception as e:
            logger.error(f"Error in get_or_create_rule_set_wrapper: {e}")
            raise e

    def save_rule_set(self, rule_set_wrapper: RuleSetWrapper) -> RuleSetWrapper:
        try:
            rule_set_wrapper.save()
            return rule_set_wrapper
        except Exception as e:
            traceback.print_exc()
            logger.error(f"Error saving rule set: {e}")
            raise e

    def delete_rule_set(self, rule_set_wrapper: RuleSetWrapper):
        try:
            rule_set_wrapper.delete()
        except Exception as e:
            logger.error(f"Error deleting rule set: {e}")
            raise e

class AnalysisService:
    def __init__(self):
        pass

    def get_revenue_and_expenses_per_period(self, revenue_expenses_query: RevenueExpensesQuery) -> Optional[
        List[ExpensesAndRevenueForPeriod]]:
        distribution_by_transaction_type_for_period_list = TransactionDistributionHandler(
            revenue_expenses_query).get_expenses_and_revenue_per_period()
        if not distribution_by_transaction_type_for_period_list or len(
                distribution_by_transaction_type_for_period_list) == 0:
            return None
        return distribution_by_transaction_type_for_period_list

    def get_revenue_and_expenses_per_period_and_category(self,
                                                         revenue_expenses_query: RevenueExpensesQuery) -> \
            Optional[RevenueAndExpensesPerPeriodAndCategory]:
        if not revenue_expenses_query:
            return None
        if revenue_expenses_query.is_empty():
            return None
        return TransactionDistributionHandler(revenue_expenses_query).get_expenses_and_revenue_per_period_and_category()

    def track_budget(self, revenue_expenses_query: RevenueExpensesQuery) -> Optional[BudgetTrackerResult]:
        if not revenue_expenses_query:
            return None
        if revenue_expenses_query.is_empty():
            return None
        budget_tree = BudgetTree.objects.get_by_bank_account(revenue_expenses_query.account_number)
        if not budget_tree:
            raise ValueError(f"Budget tree for bank account {revenue_expenses_query.account_number} does not exist")
        return BudgetTracker(revenue_expenses_query, budget_tree).get_budget_tracker_result()

    def get_category_details_for_period(self, revenue_expenses_query: RevenueExpensesQuery,
                                        category_qualified_name: str) -> CategoryDetailsForPeriodHandlerResult:
       return CategoryDetailsForPeriodHandler(revenue_expenses_query,
                                              category_qualified_name).get_category_details_for_period()

class PeriodService:
    def __init__(self):
        pass

    def resolve_start_end_date_shortcut(self, shortcut: str) -> ResolvedStartEndDateShortcut:
        shortcut = StartEndDateShortcut.from_value_string(shortcut)
        return StartEndDateShortcutResolver(shortcut).resolve()
