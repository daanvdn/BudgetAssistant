from dataclasses import dataclass, field
from typing import List, Optional

from enumfields.drf import EnumField
from rest_framework import serializers
from rest_framework.serializers import Serializer

from pybackend.analysis import ExpensesAndRevenueForPeriod, ExpensesAndRevenueForPeriodSerializer
from pybackend.commons import TransactionInContextQuery, \
    TransactionInContextQuerySerializer, TransactionQuery, \
    TransactionQuerySerializer, TransactionTypeEnum
from pybackend.models import Transaction
from pybackend.serializers import TransactionSerializer


@dataclass
class RevenueAndExpensesPerPeriodResponse:
    content: List[ExpensesAndRevenueForPeriod]
    number: int
    totalElements: int
    size: int


class RevenueAndExpensesPerPeriodResponseSerializer(Serializer):
    content = ExpensesAndRevenueForPeriodSerializer(many=True)
    number = serializers.IntegerField()
    totalElements = serializers.IntegerField()
    size = serializers.IntegerField()

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        value['content'] = [ExpensesAndRevenueForPeriodSerializer().create(item) for item in value.get('content', [])]
        return value

    def create(self, validated_data):
        content_data = validated_data.pop('content')
        content = [ExpensesAndRevenueForPeriodSerializer().create(item) for item in content_data]
        return RevenueAndExpensesPerPeriodResponse(content=content, **validated_data)


@dataclass
class TransactionsPage:
    content: List[Transaction]
    number: int
    totalElements: int
    size: int


class TransactionsPageSerializer(Serializer):
    content: List[Transaction] = TransactionSerializer(many=True)
    number: int = serializers.IntegerField()
    totalElements: int = serializers.IntegerField()
    size: int = serializers.IntegerField()

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        value['content'] = [Transaction(**transaction) for transaction in value.get('content', [])]
        return value


@dataclass
class Count:
    count: int


class CountSerializer(Serializer):
    count: int = serializers.IntegerField()


@dataclass
class SuccessfulOperationResponse:
    message: str
    status_code: int = field(default=200)


class SuccessfulOperationResponseSerializer(Serializer):
    message: str = serializers.CharField()
    status_code: int = serializers.IntegerField(default=200)


@dataclass
class FailedOperationResponse:
    error: str
    status_code: int = field(default=400)


class FailedOperationResponseSerializer(Serializer):
    error: str = serializers.CharField()
    status_code: int = serializers.IntegerField(default=400)


@dataclass
class UploadTransactionsResponse:
    created: int = 0
    updated: int = 0
    status_code: int = field(default=200)


class UploadTransactionsResponseSerializer(Serializer):
    created: int = serializers.IntegerField(min_value=0, default=0)
    updated: int = serializers.IntegerField(min_value=0, default=0)
    status_code: int = serializers.IntegerField(default=200)


@dataclass
class RegisterUser:
    username: str
    password: str
    email: str


class RegisterUserSerializer(Serializer):
    username: str = serializers.CharField()
    password: str = serializers.CharField()
    email: str = serializers.EmailField()


@dataclass
class GetOrCreateRuleSetWrapper:
    category_qualified_name: str
    type: TransactionTypeEnum


class GetOrCreateRuleSetWrapperSerializer(Serializer):
    category_qualified_name: str = serializers.CharField()
    type: TransactionTypeEnum = EnumField(TransactionTypeEnum)


@dataclass
class BasePageTransactionsRequest:
    page: Optional[int] = field(default=0)
    size: Optional[int] = field(default=10)
    sort_order: Optional[str] = field(default='asc')
    sort_property: Optional[str] = field(default='transaction_id')


@dataclass
class PageTransactionsRequest(BasePageTransactionsRequest):
    query: Optional[TransactionQuery] = field(default=None)


class BasePageTransactionsRequestSerializer(Serializer):
    page = serializers.IntegerField(default=0)
    size = serializers.IntegerField(default=10)
    sort_order = serializers.ChoiceField(default='asc', choices=['asc', 'desc'])
    sort_property = serializers.ChoiceField(default='transaction_id',
                                            choices=['transaction_id', 'booking_date', 'amount', 'counterparty',
                                                     'category', 'manually_assigned_category', 'is_recurring',
                                                     'is_advance_shared_account', 'upload_timestamp',
                                                     'is_manually_reviewed'])


class PageTransactionsRequestSerializer(BasePageTransactionsRequestSerializer):
    query = TransactionQuerySerializer(required=False)

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        serializer = TransactionQuerySerializer(data=data.get('query', {}))
        if serializer.is_valid():
            value['query'] = TransactionQuery(**serializer.validated_data)
        # value['query'] = TransactionQuery2Serializer(instance=data.get('query', {})).data
        return value


@dataclass
class PageTransactionsInContextRequest(BasePageTransactionsRequest):
    query: TransactionInContextQuery = field(default=None)


class PageTransactionsInContextRequestSerializer(BasePageTransactionsRequestSerializer):
    query = TransactionInContextQuerySerializer(required=True)


@dataclass
class PageTransactionsToManuallyReviewRequest(BasePageTransactionsRequest):
    bank_account: str = None
    transaction_type: TransactionTypeEnum = None


class PageTransactionsToManuallyReviewRequestSerializer(BasePageTransactionsRequestSerializer):
    bank_account = serializers.CharField()
    transaction_type = EnumField(TransactionTypeEnum)


class BankAccountNumberSerializer(Serializer):
    bank_account_number = serializers.CharField()


@dataclass
class SaveAlias:
    alias: str
    bank_account: str


class SaveAliasSerializer(Serializer):
    alias: str = serializers.CharField()
    bank_account: str = serializers.CharField()


class PasswordEmailSerializer(serializers.Serializer):
    password = serializers.CharField(required=False)
    email = serializers.EmailField(required=False)


@dataclass
class CategorizeTransactionsResponse:
    message: str
    with_category_count: int
    without_category_count: int


class CategorizeTransactionsResponseSerializer(Serializer):
    message = serializers.CharField()
    with_category_count = serializers.IntegerField()
    without_category_count = serializers.IntegerField()


