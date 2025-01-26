import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

from django.db.models import Q
from enumfields.drf import EnumField
from enumfields.enums import ChoicesEnum
from rest_framework import serializers
from rest_framework.serializers import Serializer

from pybackend.period import Grouping


def normalize_counterparty_name_or_account(a_string: str) -> str:
    #remove all whitespaces and convert to lowercase
    return re.sub(r'\s+', '', a_string).lower()


class RecurrenceType(str, ChoicesEnum):
    RECURRENT = 'RECURRENT'
    NON_RECURRENT = 'NON_RECURRENT'
    BOTH = 'BOTH'



class TransactionTypeEnum(str, ChoicesEnum):
    REVENUE = 'REVENUE'
    EXPENSES = 'EXPENSES'
    BOTH = 'BOTH'

    @staticmethod
    def from_value(value: str) -> 'TransactionTypeEnum':
        value = value.lower()
        if value == 'revenue':
            return TransactionTypeEnum.REVENUE
        elif value == 'expenses':
            return TransactionTypeEnum.EXPENSES
        elif value == 'both':
            return TransactionTypeEnum.BOTH
        else:
            raise ValueError(f"Invalid TransactionType value {value}")


    def __str__(self):
        #call the __str__ method of ChoicesEnum, not of the str class
        return super().__str__().upper()


@dataclass
class RevenueExpensesQuery:
    account_number: str
    transaction_type: TransactionTypeEnum
    start: datetime
    end: datetime
    grouping: Optional[Grouping]
    revenue_recurrence: Optional[RecurrenceType]
    expenses_recurrence: Optional[RecurrenceType]

    def is_empty(self):
        return all(
            field is None or (isinstance(field, str) and not field.strip())
            for field in [
                self.account_number,
                self.start,
                self.end,
                self.transaction_type,
                self.revenue_recurrence,
                self.expenses_recurrence
            ]
        )


class RevenueExpensesQuerySerializer(Serializer):
    account_number: str = serializers.CharField()
    transaction_type: TransactionTypeEnum = EnumField(TransactionTypeEnum)
    start: datetime = serializers.DateTimeField()
    end: datetime = serializers.DateTimeField()
    grouping: Grouping = EnumField(Grouping)
    revenue_recurrence: Optional[RecurrenceType] = EnumField(RecurrenceType)
    expenses_recurrence: Optional[RecurrenceType] = EnumField(RecurrenceType)


@dataclass
class TransactionQuery:
    MAX_AMOUNT: float = 1000000.0
    MIN_AMOUNT: float = -1000000.0
    revenue: bool = True
    expenses: bool = True
    counterparty_name: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    account_number: str = "NULL"
    category: Optional[str] = None  # Assuming category is a string, adjust if necessary
    transaction_or_communication: Optional[str] = None
    counterparty_account_number: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    upload_timestamp: Optional[datetime] = None
    manually_assigned_category: bool = False


class TransactionQuerySerializer(Serializer):
    revenue: bool = serializers.BooleanField()
    expenses: bool = serializers.BooleanField()
    counterparty_name: Optional[str] = serializers.CharField(required=False, default=None)
    min_amount: Optional[float] = serializers.FloatField(required=False, default=None)
    max_amount: Optional[float] = serializers.FloatField(required=False, default=None)
    account_number: str = serializers.CharField(required=True)
    category: Optional[str] = serializers.CharField(required=False, default=None)
    transaction_or_communication: Optional[str] = serializers.CharField(required=False, default=None)
    counterparty_account_number: Optional[str] = serializers.CharField(required=False, default=None)
    start_date: Optional[date] = serializers.DateField(required=False, default=None)
    end_date: Optional[date] = serializers.DateField(required=False, default=None)
    upload_timestamp: Optional[datetime] = serializers.DateTimeField(required=False, default=None)
    manually_assigned_category: bool = serializers.BooleanField(required=False, default=False)



@dataclass
class TransactionInContextQuery:
    bank_account: str
    period: str
    transaction_type: TransactionTypeEnum
    category_id: int


class TransactionInContextQuerySerializer(Serializer):
    bank_account: str = serializers.CharField()
    period: str = serializers.CharField()
    transaction_type: TransactionTypeEnum = EnumField(TransactionTypeEnum)
    category_id: int = serializers.IntegerField()


class TransactionPredicates:
    @staticmethod
    def has_period(start: datetime, end: datetime):
        return Q(booking_date__gte=start) & Q(booking_date__lte=end)

    @staticmethod
    def has_account_number(account_number: str):
        return Q(bank_account__account_number__iexact=account_number)

    @staticmethod
    def transaction_type_with_recurrence(transaction_type: TransactionTypeEnum, revenue_recurrence: RecurrenceType,
                                         expenses_recurrence: RecurrenceType):
        revenue_pred = Q(amount__gt=0.0)
        expenses_pred = Q(amount__lt=0.0)
        recurring_pred = Q(is_recurring=True)
        non_recurring_pred = Q(is_recurring=False)

        if transaction_type == TransactionTypeEnum.REVENUE:
            if revenue_recurrence == RecurrenceType.RECURRENT:
                return revenue_pred & recurring_pred
            elif revenue_recurrence == RecurrenceType.NON_RECURRENT:
                return revenue_pred & non_recurring_pred
            else:
                return revenue_pred
        elif transaction_type == TransactionTypeEnum.EXPENSES:
            if expenses_recurrence == RecurrenceType.RECURRENT:
                return expenses_pred & recurring_pred
            elif expenses_recurrence == RecurrenceType.NON_RECURRENT:
                return expenses_pred & non_recurring_pred
            else:
                return expenses_pred
        elif transaction_type == TransactionTypeEnum.BOTH:
            revenue_pred = TransactionPredicates.transaction_type_with_recurrence(TransactionTypeEnum.REVENUE,
                                                                                  revenue_recurrence,
                                                                                  RecurrenceType.BOTH)
            expenses_pred = TransactionPredicates.transaction_type_with_recurrence(TransactionTypeEnum.EXPENSES,
                                                                                   RecurrenceType.BOTH,
                                                                                   expenses_recurrence)
            return revenue_pred | expenses_pred
        else:
            raise ValueError("Unexpected transaction type")

    @staticmethod
    def has_account_number_and_transaction_type(account_number: str, transaction_type: TransactionTypeEnum):
        account_number_pred = TransactionPredicates.has_account_number(account_number)
        transaction_type_pred = TransactionPredicates.has_transaction_type(transaction_type)
        return account_number_pred & transaction_type_pred
    @staticmethod
    def has_period_account_number_and_is_revenue(revenue_expenses_query: RevenueExpensesQuery):
        period_pred = TransactionPredicates.has_period(revenue_expenses_query.start, revenue_expenses_query.end)
        account_number_pred = TransactionPredicates.has_account_number(revenue_expenses_query.account_number)
        is_revenue_pred = TransactionPredicates.transaction_type_with_recurrence(
            revenue_expenses_query.transaction_type,
            revenue_expenses_query.revenue_recurrence,
            revenue_expenses_query.expenses_recurrence
        )
        return period_pred & account_number_pred & is_revenue_pred

    @staticmethod
    def requires_manual_review(bank_account, transaction_type: TransactionTypeEnum) -> Q:

        manually_assigned_q = Q(manually_assigned_category=False) | Q(manually_assigned_category__isnull=True)
        category_is_null_q = Q(category__isnull=True)
        account_number_q = Q(bank_account__account_number=bank_account.account_number)
        if transaction_type == TransactionTypeEnum.BOTH:
            return manually_assigned_q & category_is_null_q & account_number_q
        else:
            transaction_type_q = Q(amount__gte=0.0) if transaction_type == TransactionTypeEnum.REVENUE else Q(amount__lt=0.0)
            return manually_assigned_q & category_is_null_q & transaction_type_q & account_number_q

    @staticmethod
    def from_transaction_query(transaction_query: TransactionQuery) -> Optional[Q]:
        predicates = []
        predicates.append(TransactionPredicates.upload_time_stamp_query(transaction_query.upload_timestamp))
        predicates.append(TransactionPredicates.amount_predicate(transaction_query))
        predicates.append(TransactionPredicates.category_predicate(transaction_query))
        predicates.append(TransactionPredicates.account_number_predicate(transaction_query))
        predicates.append(TransactionPredicates.counterparty_account_number_predicate(transaction_query))
        predicates.append(TransactionPredicates.date_range_predicate(transaction_query))
        predicates.append(TransactionPredicates.counterparty_predicate(transaction_query))
        predicates.append(TransactionPredicates.free_text_predicate(transaction_query))
        #now we need to filter out the None values
        predicates = [predicate for predicate in predicates if predicate is not None]
        if len(predicates) == 0:
            return Q()  # No specific filter
        #combine all the predicates with AND. Not OR
        combined_q = Q()  # Start with an empty Q object
        for q in predicates:
            combined_q &= q  # Combine using AND

        return combined_q

    @staticmethod
    def from_transaction_in_context_query(transaction_query: TransactionInContextQuery) -> Optional[Q]:
        predicates = []
        predicates.append(TransactionPredicates.has_account_number(transaction_query.bank_account))
        predicates.append(TransactionPredicates.transaction_type(transaction_query.transaction_type))
        predicates.append(TransactionPredicates.category_id_predicate(transaction_query.category_id))
        #now we need to filter out the None values
        predicates = [predicate for predicate in predicates if predicate is not None]
        if len(predicates) == 0:
            return Q()
        #combine all the predicates with AND. Not OR
        combined_q = Q()  # Start with an empty Q object
        for q in predicates:
            combined_q &= q  # Combine using AND

        return combined_q

    @staticmethod
    def free_text_predicate(transaction_query):
        free_text = transaction_query.transaction_or_communication
        if not free_text:
            return None

        search_string = f"%{free_text.strip()}%"
        return Q(counterparty__name__icontains=search_string) | Q(communications__icontains=search_string) | Q(transaction__icontains=search_string)
    @staticmethod
    def counterparty_predicate(transaction_query):
        counterparty_name = transaction_query.counterparty_name
        if counterparty_name is None or counterparty_name.strip().upper() == "NULL":
            return None
        return Q(counterparty__name__icontains=counterparty_name.strip())
    @staticmethod
    def date_range_predicate(transaction_query: TransactionQuery) -> Optional[Q]:
        start_date = transaction_query.start_date
        end_date = transaction_query.end_date
        if start_date is None or end_date is None:
            return None
        return Q(booking_date__range=(start_date, end_date))

    @staticmethod
    def counterparty_account_number_predicate(transaction_query):
        counterparty_account_number = transaction_query.counterparty_account_number
        if counterparty_account_number is None or counterparty_account_number.strip().upper() == "NULL":
            return None
        return Q(counterparty__account_number__iexact=counterparty_account_number.strip())

    @staticmethod
    def upload_time_stamp_query(upload_timestamp: datetime) -> Optional[Q]:
        if not upload_timestamp:
            return None
        return Q(upload_timestamp__eq=upload_timestamp)

    @staticmethod
    def has_transaction_type(transaction_type: TransactionTypeEnum) -> Q:
        if transaction_type == TransactionTypeEnum.REVENUE:
            return Q(amount__gt=0.0)
        if transaction_type == TransactionTypeEnum.EXPENSES:
            return Q(amount__lt=0.0)
        if transaction_type == TransactionTypeEnum.BOTH:
            return Q()
        raise ValueError("Unexpected transaction type")


    @staticmethod
    def amount_predicate(transaction_query: TransactionQuery) -> Q:
        is_revenue = transaction_query.revenue
        is_expenses = transaction_query.expenses
        min_amount = transaction_query.min_amount
        max_amount = transaction_query.max_amount

        if min_amount is not None and max_amount is not None:
            return Q(amount__gte=min_amount) & Q(amount__lte=max_amount)

        if is_revenue and is_expenses:
            return Q()  # No specific filter, equivalent to Optional.empty() in Java

        if is_revenue:
            return Q(amount__gt=0.0)

        if is_expenses:
            return Q(amount__lt=0.0)

        return Q()  # Default case if none of the conditions are met

    @staticmethod
    def transaction_type(transaction_type: TransactionTypeEnum):
        if transaction_type == TransactionTypeEnum.REVENUE:
            return Q(amount__gt=0.0)
        if transaction_type == TransactionTypeEnum.EXPENSES:
            return Q(amount__lt=0.0)
        if transaction_type == TransactionTypeEnum.BOTH:
            return Q()
        raise ValueError("Unexpected transaction type")
    @staticmethod
    def category_predicate(transaction_query: TransactionQuery) -> Optional[Q]:
        category:str = transaction_query.category
        if category is None or category in ["DUMMY_CATEGORY_NAME", "NO_CATEGORY_NAME"]:
            return None
        return Q(category__qualified_name=category) #fix this query
    @staticmethod
    def category_id_predicate(category_id: int) -> Optional[Q]:
        if category_id is None:
            return None
        return Q(category__id=category_id)
    @staticmethod
    def account_number_predicate(transaction_query: TransactionQuery) -> Optional[Q]:
        account_number = transaction_query.account_number
        if account_number is None or account_number.strip().upper() == "NULL":
            return None
        return Q(bank_account__account_number__iexact=account_number.strip())

    @staticmethod
    def has_period_account_number_and_is_revenue_and_category_is_null(revenue_expenses_query: RevenueExpensesQuery):
        categories_predicate = Q(category__isnull=True)
        account_number = revenue_expenses_query.account_number
        transaction_type = revenue_expenses_query.transaction_type
        period_pred = TransactionPredicates.has_period(revenue_expenses_query.start, revenue_expenses_query.end)
        account_number_pred = TransactionPredicates.has_account_number(account_number)
        is_revenue_pred = TransactionPredicates.transaction_type_with_recurrence(
            transaction_type,
            revenue_expenses_query.revenue_recurrence,
            revenue_expenses_query.expenses_recurrence
        )

        combined_predicate = period_pred & account_number_pred & is_revenue_pred & categories_predicate
        return combined_predicate

    @staticmethod
    def has_period_account_number_and_is_revenue_and_has_category(revenue_expenses_query: RevenueExpensesQuery, categories):
        categories_predicate = Q(category__id__in=categories)
        account_number = revenue_expenses_query.account_number
        transaction_type = revenue_expenses_query.transaction_type
        period_pred = TransactionPredicates.has_period(revenue_expenses_query.start, revenue_expenses_query.end)
        account_number_pred = TransactionPredicates.has_account_number(account_number)
        is_revenue_pred = TransactionPredicates.transaction_type_with_recurrence(
            transaction_type,
            revenue_expenses_query.revenue_recurrence,
            revenue_expenses_query.expenses_recurrence
        )

        combined_predicate = period_pred & account_number_pred & is_revenue_pred & categories_predicate
        return combined_predicate



@dataclass
class RevenueExpensesQueryWithCategory(RevenueExpensesQuery):
    category: str


class RevenueExpensesQueryWithCategorySerializer(RevenueExpensesQuerySerializer):
    category = serializers.CharField()
