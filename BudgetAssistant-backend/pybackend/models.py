import datetime
import hashlib
import json
import re
from typing import List

from django.contrib.auth.models import AbstractUser
from django.db import IntegrityError, models
from django.utils import timezone
from enumfields import CharEnumField

from pybackend.commons import TransactionTypeEnum
from pybackend.db import BankAccountManager, BudgetTreeManager, BudgetTreeNodeManager, CategoryManager, \
    CategoryTreeManager, CounterpartyManager, TransactionManager, UserManager


class RequiredFieldsMixin:
    def save(self, *args, **kwargs):
        # Validate required fields before saving
        self.validate_required_fields()
        super().save(*args, **kwargs)
        return self

    def validate_required_fields(self):
        #check if self has _meta attribute
        if not hasattr(self, '_meta'):
            raise AttributeError("Model does not have '_meta' attribute.")
        for field in self._meta.fields:
            if not field.blank and not field.null:
                value = getattr(self, field.name)
                if value is None:
                    raise IntegrityError(f"Field '{field.name}' is required.")
                elif isinstance(value, str) and value.strip() == "":
                    raise IntegrityError(f"Field '{field.name}' is required.")


class BankAccount(RequiredFieldsMixin, models.Model):
    account_number = models.CharField(max_length=255, primary_key=True)
    users = models.ManyToManyField('CustomUser', related_name='associated_bank_accounts')
    alias = models.CharField(max_length=255, blank=True, null=True)
    objects = BankAccountManager()

    def __str__(self):
        return self.account_number

    def to_json(self):
        return {
            "account_number": self.account_number,
            "alias": self.alias
        }

    @staticmethod
    def normalize_account_number(account_number):
        return account_number.replace(" ", "").lower()


class CustomUser(RequiredFieldsMixin, AbstractUser):
    bank_accounts = models.ManyToManyField('BankAccount', related_name='custom_users')
    objects = UserManager()

    def __str__(self):
        return self.username

    def to_json(self):
        return {
            "username": self.username,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "password": self.password
        }


class Transaction(RequiredFieldsMixin, models.Model):
    transaction_id = models.CharField(max_length=64, primary_key=True, unique=True, blank=False, null=False)
    bank_account = models.ForeignKey('BankAccount', on_delete=models.CASCADE, blank=False, null=False)
    booking_date = models.DateField(blank=False, null=False)
    statement_number = models.TextField(blank=False, null=False)
    counterparty = models.ForeignKey('Counterparty', on_delete=models.CASCADE, blank=False, null=False)
    transaction_number = models.TextField(unique=True, blank=False, null=False)
    transaction = models.TextField(blank=True, null=True)
    currency_date = models.DateField(blank=False, null=False)
    amount = models.FloatField(blank=False, null=False)
    currency = models.CharField(max_length=255, blank=False, null=False)
    bic = models.CharField(max_length=255, blank=True, null=True)
    country_code = models.CharField(max_length=255, blank=False, null=False)
    communications = models.TextField(blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank=True, null=True)
    manually_assigned_category = models.BooleanField(default=False, blank=True, null=True)
    is_recurring = models.BooleanField(default=False, blank=True, null=True)
    is_advance_shared_account = models.BooleanField(default=False, blank=True, null=True)
    upload_timestamp = models.DateTimeField(default=datetime.datetime.now(), blank=False, null=False)
    is_manually_reviewed = models.BooleanField(default=False, blank=True, null=True)
    objects = TransactionManager()




    def __str__(self):
        return self.transaction_id

    def has_category(self) -> bool:
        return self.category is not None

    def get_transaction_type(self) -> TransactionTypeEnum:
        if self.amount >= 0.0:
            return TransactionTypeEnum.REVENUE
        return  TransactionTypeEnum.EXPENSES

    def to_json_str(self) -> str:
        return json.dumps(self)


    def save(self, *args, **kwargs):
        self.transaction_id = Transaction._create_transaction_id(self.transaction_number, self.bank_account)
        return super().save(*args, **kwargs)

    @staticmethod
    def _create_transaction_id(transaction_number:str, bank_account: BankAccount) -> str:
        raw_value = '_'.join([transaction_number, str(hash(bank_account.account_number))])
        return hashlib.sha256(raw_value.encode()).hexdigest()[:64]  # Trim if needed



    # def to_csv(self) ->List[str]:
    #     return [
    #         self.bank_account.account_number,
    #         self.booking_date,
    #         self.statement_number,
    #         self.transaction_number,
    #         self.counterparty.account_number,
    #         self.counterparty.name,
    #         self.counterparty.street_and_number,
    #         self.counterparty.zip_code_and_city,
    #         self.transaction,
    #         self.currency_date,
    #         str(self.amount),
    #         self.currency,
    #         self.bic,
    #         self.country_code,
    #         self.communications
    #     ]


class Counterparty(models.Model, RequiredFieldsMixin):
    name = models.CharField(max_length=255, primary_key=True)
    account_number = models.TextField(blank=False, null=False)
    street_and_number = models.TextField(blank=True, null=True)
    zip_code_and_city = models.TextField(blank=True, null=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank=True, null=True)
    users = models.ManyToManyField('CustomUser', related_name='counterparties', blank=False)

    objects = CounterpartyManager()  # Custom manager

    def __str__(self):
        return self.name

    @staticmethod
    def normalize_counterparty(counterparty_name):
        return re.sub(r'\s{2,}', ' ', counterparty_name.strip().lower())

    def save(self, *args, **kwargs):
        self.name = self.normalize_counterparty(self.name)
        super().save(*args, **kwargs)


class CategoryTree(models.Model):
    id = models.AutoField(primary_key=True)
    root = models.OneToOneField('Category', on_delete=models.CASCADE)
    type = CharEnumField(TransactionTypeEnum)

    objects = CategoryTreeManager()  # Custom manager

    def __str__(self):
        return f"{self.type} - {self.root.name}"


class Category(models.Model):
    ROOT_NAME = "root"
    NO_CATEGORY_NAME = "NO CATEGORY"
    DUMMY_CATEGORY_NAME = "DUMMY CATEGORY"

    id = models.AutoField(primary_key=True)
    name = models.TextField(null=False, blank=False)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )
    is_root = models.BooleanField(default=False)
    qualified_name = models.TextField(null=False, blank=False)
    type = CharEnumField(TransactionTypeEnum)
    _children_cache = None
    objects = CategoryManager()

    def __str__(self):
        return self.name

    def add_child(self, child):
        child.parent = self
        child.save()

    def __hash__(self):
        if not self.qualified_name:
            raise ValueError("Qualified name is not set.")
        return hash(self.qualified_name)

    def __eq__(self, other):
        if not self.qualified_name:
            raise ValueError("Qualified name is not set.")
        else:
            if not other.qualified_name:
                raise ValueError("Qualified name is not set.")
        return self.qualified_name == other.qualified_name

    def __lt__(self, other):
        return self.qualified_name < other.qualified_name

    def __gt__(self, other):
        return self.qualified_name > other.qualified_name

    @staticmethod
    def no_category_object():
        return Category(id=-1, name=Category.NO_CATEGORY_NAME, is_root=False)

    @property
    def cached_children(self):
        """Return cached children if available, else fetch and cache them."""
        if self._children_cache is None:
            self._children_cache = list(self.children.all())
        return self._children_cache




class BudgetTree(models.Model, RequiredFieldsMixin):
    #id = models.AutoField(primary_key=True)
    bank_account = models.OneToOneField('BankAccount', blank=False, null=False, primary_key=True, on_delete=models.CASCADE)
    root: 'BudgetTreeNode' = models.OneToOneField('BudgetTreeNode', on_delete=models.CASCADE)
    number_of_descendants = models.IntegerField(default=0)
    objects = BudgetTreeManager()
    _children_cache = None


    def __str__(self):
        return self.bank_account.account_number


    @property
    def cached_children(self):
        """Return cached children if available, else fetch and cache them."""
        if self._children_cache is None:
            self._children_cache = list(self.root.children.all())
        return self._children_cache


class BudgetTreeNode(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.ForeignKey('Category', on_delete=models.SET_NULL, blank=True, null=True)
    amount = models.IntegerField(default=0)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    objects = BudgetTreeNodeManager()
    _children_cache = None


    def __str__(self):
        return f"{self.category.name} - {self.amount}"


    @property
    def cached_children(self) -> List['BudgetTreeNode']:
        """Return cached children if available, else fetch and cache them."""
        if self._children_cache is None:
            self._children_cache = list(self.children.all())
        return self._children_cache

    def add_child(self, child):
        child.parent = self
        child.save()

    def is_root_category(self) -> bool:
        return self.category.name == Category.ROOT_NAME

    def  parent_node_is_root(self) -> bool:
        return self.parent.category.name == Category.ROOT_NAME

    def __eq__(self, other):
        # id, category, amount
        return self.id == other.id and self.category == other.category and self.amount == other.amount

    def __hash__(self):
        #id, category, amount
        return hash((self.id, self.category, self.amount))



class TreeNode(models.Model):
    name = models.CharField(max_length=100)
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True, related_name='children'
    )

    def __str__(self):
        return self.name
