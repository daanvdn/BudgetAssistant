from abc import abstractmethod
from datetime import datetime
from typing import Dict, Generic, List, Optional, TypeVar, Union

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from pybackend.models import BankAccount, Category, Counterparty, CustomUser, Transaction
from .models import BudgetTree, BudgetTreeNode, CategoryTree

T = TypeVar('T')


class DeserializeInstanceMixin(serializers.ModelSerializer):
    def deserialize_instance(self, data:Dict, pk):
        # Step 1: Retrieve the existing instance from the database using the primary key
        instance = self.Meta.model.objects.get(pk=pk)

        # Step 2: Create a serializer object with the instance and data
        serializer = self.__class__(instance, data=data)

        # Step 3: Check if the serializer is valid and update the instance
        if serializer.is_valid():
            updated_instance = serializer.update(instance, serializer.validated_data)
            return updated_instance
        else:
            raise serializers.ValidationError(serializer.errors)

class CustomUserSerializer(DeserializeInstanceMixin):

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'password', 'bank_accounts']
        extra_kwargs = {'password': {'write_only': True}, 'bank_accounts': {'required': False}}

    def create(self, validated_data):
        # Extract bank accounts data
        bank_accounts_data = validated_data.pop('bank_accounts', [])

        # Create the user instance
        user = CustomUser.objects.create(**validated_data)

        # Process bank accounts
        for bank_account in bank_accounts_data:
            # Get or create the bank account by account_number
            bank_account, created = BankAccount.objects.get_or_create(bank_account)
            bank_account.users.add(user)
            user.bank_accounts.add(bank_account)
        return user

    def update(self, instance: CustomUser, validated_data: Dict):
        # Extract bank accounts data
        bank_accounts = validated_data.pop('bank_accounts', [])

        # Update the user instance
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()

        # Process bank accounts
        for bank_account in bank_accounts:
            # Get or create the bank account by account_number
            bank_account, created = BankAccount.objects.get_or_create(bank_account)
            # Associate the user with the bank account
            bank_account.users.add(instance)
            instance.bank_accounts.add(bank_account)
            bank_account.save()

        return instance


class BankAccountSerializer(DeserializeInstanceMixin):
    class Meta:
        model = BankAccount
        fields = ['account_number', 'alias', 'users']

    def create(self, validated_data):
        users_data = validated_data.pop('users', [])
        bank_account = BankAccount.objects.create(**validated_data)
        for user in users_data:
            # Get or create the bank account by account_number
            user, created = CustomUser.objects.get_or_create(user)
            bank_account.users.add(user)
            user.bank_accounts.add(bank_account)
        return bank_account

    def update(self, instance: BankAccount, validated_data: Dict):
        users_data = validated_data.pop('users', [])
        instance.account_number = BankAccount.normalize_account_number(
            validated_data.get('account_number', instance.account_number))
        instance.alias = validated_data.get('alias', instance.alias)
        instance.save()
        for user in users_data:
            # Get or create the bank account by account_number
            user, created = CustomUser.objects.get_or_create(username=user)

            # Associate the user with the bank account
            instance.users.add(user)
            # Associate the bank account with the user
            user.bank_accounts.add(instance)
            user.save()

        return instance



class CategorySerializer(DeserializeInstanceMixin):
    type = serializers.CharField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['name', 'qualified_name', 'type', 'children']
        # children can be empty, so we need to set required to False
        extra_kwargs = {'children': {'required': False}}

    def get_children(self, obj):
        children = obj.cached_children
        return CategorySerializer(children, many=True).data

class SimpleCategorySerializer(serializers.Serializer):
    qualified_name = serializers.CharField(required=True)
    name = serializers.CharField(required=True)
    id = serializers.IntegerField(required=True)

    class Meta:
        model = Category
        fields = ['qualified_name', 'name', 'id']


    def create(self, validated_data):
        return Category.objects.get(id=validated_data['id'])


class CounterpartySerializer(DeserializeInstanceMixin):
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False, allow_null=True)
    users = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.all(), many=True, required=False, allow_null=True)


    class Meta:
        model = Counterparty
        fields = ['name', 'account_number', 'street_and_number', 'zip_code_and_city', 'category', 'users']

        extra_kwargs = {'users': {'required': False}, 'category': {'required': False}}


    def create(self, validated_data):
        users_data = validated_data.pop('users', [])
        category = validated_data.pop('category', None)
        counterparty = Counterparty.objects.create(**validated_data)
        counterparty.category = category
        counterparty.save()
        counterparty.users.set(users_data)
        return counterparty

    def update(self, instance, validated_data):
        users_data = validated_data.pop('users', [])
        category = validated_data.pop('category', None)
        instance.name = validated_data.get('name', instance.name)
        instance.account_number = validated_data.get('account_number', instance.account_number)
        instance.street_and_number = validated_data.get('street_and_number', instance.street_and_number)
        instance.zip_code_and_city = validated_data.get('zip_code_and_city', instance.zip_code_and_city)
        instance.category = category
        instance.save()
        for user in users_data:
            user, created = CustomUser.objects.get_or_create(username=user)
            instance.users.add(user)
            user.counterparties.add(instance)
        return instance

class TransactionSerializer(DeserializeInstanceMixin):
    transaction_id: str = serializers.CharField(required=True)
    category = SimpleCategorySerializer(required=False, allow_null=True)
    bank_account = serializers.PrimaryKeyRelatedField(queryset=BankAccount.objects.all(), required=False)
    counterparty = serializers.PrimaryKeyRelatedField(queryset=Counterparty.objects.all(), required=False)
    booking_date = serializers.DateField(format="%d/%m/%Y",
                                         input_formats=["%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d"], required=False)
    currency_date = serializers.DateField(format="%d/%m/%Y",
                                          input_formats=["%d/%m/%Y", "%d-%m-%Y", "%Y/%m/%d", "%Y-%m-%d", 'iso-8601'])
    upload_timestamp: datetime = serializers.DateTimeField(format='%Y-%m-%dT%H:%M:%S.%fZ' , input_formats=['%Y-%m-%dT%H:%M:%S.%fZ', 'iso-8601'], required=False)

    statement_number: str = serializers.CharField(required=False)
    transaction_number: str = serializers.CharField(required=False)
    transaction: Optional[str] = serializers.CharField(allow_null=True, required=False)
    amount: float = serializers.FloatField(required=False)
    currency: str = serializers.CharField(required=False)
    bic: Optional[str] = serializers.CharField(allow_null=True, required=False)
    country_code: str = serializers.CharField(required=False)
    communications: Optional[str] = serializers.CharField(allow_null=True)
    manually_assigned_category: Optional[bool] = serializers.BooleanField(allow_null=True, required=False)
    is_recurring: Optional[bool] = serializers.BooleanField(allow_null=True, required=False)
    is_advance_shared_account: Optional[bool] = serializers.BooleanField(allow_null=True, required=False)
    is_manually_reviewed: Optional[bool] = serializers.BooleanField(allow_null=True, required=False)

    class Meta:
        model = Transaction
        fields = [
            'transaction_id', 'bank_account', 'booking_date', 'statement_number', 'counterparty',
            'transaction_number', 'transaction', 'currency_date', 'amount', 'currency', 'bic',
            'country_code', 'communications', 'category', 'manually_assigned_category', 'is_recurring',
            'is_advance_shared_account', 'upload_timestamp', 'is_manually_reviewed'
        ]
        # category can be empty, so we need to set required to False
        extra_kwargs = {'category': {'required': False}, 'manually_assigned_category': {'required': False},
                        'is_recurring': {'required': False}, 'is_advance_shared_account': {'required': False},
                        'is_manually_reviewed': {'required': False}, 'communications': {'required': False},
                        'transaction': {'required': False}, 'bic': {'required': False}}



    def update(self, instance, validated_data):
        if validated_data.get('category'):
            category= SimpleCategorySerializer().create(validated_data.pop('category'))
            # Add the category to the transaction
            instance.category = category
            category.save()
        if 'manually_assigned_category' in validated_data:
            instance.manually_assigned_category = validated_data.get('manually_assigned_category')
        if 'is_recurring' in validated_data:
            instance.is_recurring = validated_data.get('is_recurring')
        if 'is_advance_shared_account' in validated_data:
            instance.is_advance_shared_account = validated_data.get('is_advance_shared_account')
        if 'is_manually_reviewed' in validated_data:
            instance.is_manually_reviewed = validated_data.get('is_manually_reviewed')
        saved = instance.save()
        return saved

    def create(self, validated_data):
        category_data = validated_data.pop('category', None)
        if category_data:
            category = SimpleCategorySerializer().create(category_data)
            validated_data['category'] = category
        else:
            validated_data['category'] = None
        transaction = Transaction(**validated_data)
        return transaction

class SimplifiedCategorySerializer(DeserializeInstanceMixin):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['name', 'qualified_name', 'children', 'id']

    def get_children(self, obj) -> List[Dict[str, Union[str, List]]]:
        children = obj.cached_children
        return SimplifiedCategorySerializer(children, many=True).data


class CategoryTreeSerializer( DeserializeInstanceMixin):
    root = SimplifiedCategorySerializer()

    class Meta:
        model = CategoryTree
        fields = ['type', 'root']


class BudgetTreeNodeSerializer(DeserializeInstanceMixin):
    name = serializers.SerializerMethodField()
    qualified_name = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()
    budget_tree_node_id = serializers.SerializerMethodField()
    budget_tree_node_amount = serializers.SerializerMethodField()

    class Meta:
        model = BudgetTreeNode
        fields = ['name', 'qualified_name', 'budget_tree_node_id', 'budget_tree_node_amount', 'children']

    @extend_schema_field(serializers.ListField(child=serializers.DictField()))
    def get_children(self, obj) -> List[Dict]:
        children = obj.cached_children
        return BudgetTreeNodeSerializer(children, many=True).data
    def get_name(self, obj) -> str:
        return obj.category.name
    def get_qualified_name(self, obj) -> str:
        return obj.category.qualified_name
    def get_budget_tree_node_id(self, obj) -> int:
        return obj.id
    def get_budget_tree_node_amount(self, obj) -> int:
        return obj.amount


class BudgetTreeSerializer(DeserializeInstanceMixin):
    root = BudgetTreeNodeSerializer()

    class Meta:
        model = BudgetTree
        fields = '__all__'

