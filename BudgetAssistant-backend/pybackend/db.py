import logging

from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import UserManager as DjangoUserManager
from django.core.exceptions import ObjectDoesNotExist
from django.db import models

from pybackend.commons import RevenueExpensesQuery, TransactionPredicates, TransactionTypeEnum, \
    normalize_counterparty_name_or_account

logger = logging.getLogger(__name__)
class BankAccountManager(models.Manager):

    def get_or_create_bank_account(self, account_number, user):
        account_number = normalize_counterparty_name_or_account(account_number)
        bank_account, created = self.get_or_create(account_number=account_number)
        if created:
            bank_account.users.add(user)
        elif user not in bank_account.users.all():
            bank_account.users.add(user)
        return bank_account

    def normalize_account_number(self, account_number: str) -> str:
        return account_number.replace(" ", "").lower()

    def find_distinct_by_users_contains(self, user):
        return self.filter(users=user).distinct()

    def get(self, *args, **kwargs):
        if 'account_number' in kwargs:
            kwargs['account_number'] = self.normalize_account_number(kwargs['account_number'])
        return super().get(*args, **kwargs)


class BudgetTreeNodeManager(models.Manager):
    def get_budget_entry_with_children(self, id):
        return self.prefetch_related('children').get(id=id)

    def find_by_bank_account_number(self, bank_account_number):
        return self.filter(bank_account__account_number=bank_account_number).first()


class CategoryManager(models.Manager):
    def find_by_id_with_children(self, category_id):
        """
        Fetch the TreeNode with the specified ID, along with all its descendants.
        Cache the children of each node recursively.
        """
        # Get the root node for the given ID
        try:
            category = self.get(id=category_id)
        except ObjectDoesNotExist:
            return None

        # Start building the cache of descendants for the ctegory
        self._cache_descendants(category)
        return category
    def _cache_descendants(self, category):
        """
        Recursively fetch and cache children of the node and all its descendants.
        """
        # Retrieve and cache children for the given node
        children = list(category.children.all())
        category._children_cache = children

        # Recursively cache each child’s children
        for child in children:
            self._cache_descendants(child)

    def find_by_qualified_name_with_children(self, qualified_name):
        """
        Fetch the TreeNode with the specified qualified name, along with all its descendants.
        Cache the children of each node recursively.
        """
        # Get the root node for the given qualified name
        try:
            category = self.get(qualified_name=qualified_name)
        except ObjectDoesNotExist:
            return None

        # Start building the cache of descendants for the category
        self._cache_descendants(category)
        return category



class CategoryTreeManager(models.Manager):

    def find_category_tree_by_type(self, type):
        if type not in [TransactionTypeEnum.EXPENSES, TransactionTypeEnum.REVENUE]:
            raise ValueError(f"Type {type} is not a valid category type.")
        return self.filter(type=type).first()


class CounterpartyManager(models.Manager):
    def find_distinct_by_users_contains(self, user):
        return self.filter(users=user).distinct()

    def get_or_create_counterparty(self, name:str, user, account_number:str, street_and_number:str, zip_code_and_city:str):

        counterparty, created = self.get_or_create(name=name)
        if created:
            counterparty.users.add(user)
            counterparty.account_number = account_number
            counterparty.street_and_number = street_and_number
            counterparty.zip_code_and_city = zip_code_and_city
            counterparty.save()
        elif user not in counterparty.users.all():
            counterparty.users.add(user)
        return counterparty


class TransactionManager(models.Manager):

    def find_distinct_counterparty_names(self, account:str=None):
        if account:
            queryset= self.get_queryset().filter(bank_account__account_number=account)
        else:
            queryset= self.get_queryset()
        return queryset.values_list('counterparty__name', flat=True).distinct()

    def find_distinct_category_entities(self):
        return self.get_queryset().values_list('category__name', flat=True).distinct()

    def find_distinct_categories_by_name(self, category_name):
        return self.get_queryset().filter(category__name=category_name).values_list('category__name',
                                                                                    flat=True).distinct()

    def find_all_by_upload_timestamp(self, timestamp):
        return self.get_queryset().filter(upload_timestamp=timestamp)

    def find_distinct_counterparty_account_numbers(self, account:str=None):
        if account:
            queryset= self.get_queryset().filter(bank_account__account_number=account)
        else:
            queryset= self.get_queryset()

        return queryset.values_list('counterparty__account_number', flat=True).distinct()

    def find_all_by_bank_account_and_manually_assigned_category(self, bank_account, manually_assigned):
        return self.get_queryset().filter(bank_account=bank_account, manually_assigned_category=manually_assigned)

    def find_all_to_manually_review(self):
        return self.get_queryset().filter(is_manually_reviewed=False)

    def count_transaction_to_manually_review(self):
        return self.get_queryset().filter(is_manually_reviewed=False).count()

    def find_distinct_categories_by_bank_account_and_type(self, bank_account: 'BankAccount', transaction_type):
        predicate = TransactionPredicates.has_account_number_and_transaction_type(bank_account, transaction_type)
        return self.get_queryset().filter(predicate).values_list(
            'category__name', flat=True).distinct()

    def find_by_has_period_account_number_and_is_revenue(self, revenue_expenses_query: RevenueExpensesQuery):
        predicate = TransactionPredicates.has_period_account_number_and_is_revenue(revenue_expenses_query)
        transactions = self.filter(predicate)
        return transactions



class UserManager(DjangoUserManager):
    def find_user_by_username_and_password(self, username, password):
        try:
            user = self.get(username=username)
            if check_password(password, user.password):
                return user
        except self.model.DoesNotExist:
            return None

    def find_user_if_valid(self, username, password):
        user = self.find_user_by_username_and_password(username, password)
        if user:
            return user
        return None

    def find_user_by_username(self, username):
        try:
            return self.get(username=username)
        except self.model.DoesNotExist:
            return None


class BudgetTreeManager(models.Manager):
    def get_by_bank_account(self, bank_account) -> 'BudgetTree':
        if bank_account is None:
            raise ValueError("Bank account cannot be None.")
        return self.get(bank_account=bank_account)

    def exists_by_bank_account(self, bank_account) -> bool:
        return self.filter(bank_account=bank_account).exists()


class RuleSetWrapperManager(models.Manager):
    def exists_by_category_and_user(self, category, user):
        return self.filter(category=category, users=user).exists()

    def find_by_type_and_category_and_user(self, type, user, category):
        return self.filter(category__type=type, users=user, category=category).first()

    def find_by_user(self, user):
        return self.filter(users=user)
