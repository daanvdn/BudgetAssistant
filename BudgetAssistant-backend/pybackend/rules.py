import json
import re
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, ClassVar, Dict, List, Literal, Optional, Union

import networkx as nx
from django.db import models
from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.utils import extend_schema_field
from enumfields.drf import EnumField
from rest_framework import serializers
from rest_framework.serializers import Serializer

from pybackend.commons import TransactionTypeEnum
from pybackend.db import RuleSetWrapperManager
from pybackend.models import Category, CategoryTree, CustomUser, Transaction
from pybackend.serializers import DeserializeInstanceMixin, SimpleCategorySerializer

OperatorName = Literal['contains', 'exact match', 'fuzzy match']

FieldType = Literal["number", "string", "categorical"]

MatchTypeOptions = Literal["any of", "all of"]

Condition = Literal["AND", "OR"]

Clazz = Literal['Rule', 'RuleSet']

TransactionField = Literal[
    'communications', 'transaction', 'currency', 'country_code', 'counterparty.name', 'counterparty.account_number', 'bank_account.account_number', 'amount']


@dataclass
class RuleMatchType:
    name: MatchTypeOptions
    value: MatchTypeOptions

    @staticmethod
    def from_name(name: MatchTypeOptions):
        if name == "any of":
            return RuleMatchType(name=name, value="any of")
        elif name == "all of":
            return RuleMatchType(name=name, value="all of")
        else:
            raise ValueError(f"Invalid name: {name}")

    def __eq__(self, __value):
        if not isinstance(__value, RuleMatchType):
            return False
        return self.name == __value.name and self.value == __value.value

    def __hash__(self):
        return hash((self.name, self.value))


class RuleMatchTypeSerializer(Serializer):
    name = serializers.CharField()
    value = serializers.CharField()

    class Meta:
        model = RuleMatchType
        fields = '__all__'

    def create(self, validated_data):
        return RuleMatchType(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.value = validated_data.get('value', instance.value)
        return instance


ANY_OF = RuleMatchType.from_name('any of')
ALL_OF = RuleMatchType.from_name('all of')

RuleMatchTypes = Union[ANY_OF, ALL_OF]


@dataclass
class RuleOperator:
    name: OperatorName
    value: str
    type: FieldType

    @staticmethod
    def create(name: OperatorName, type: FieldType):
        return RuleOperator(name=name, value=name, type=type)

    def __eq__(self, __value):
        if not isinstance(__value, RuleOperator):
            return False
        return self.name == __value.name and self.value == __value.value and self.type == __value.type

    def __hash__(self):
        return hash((self.name, self.value, self.type))


class RuleOperatorSerializer(Serializer):
    name = serializers.CharField()
    value = serializers.CharField()
    type = serializers.CharField()

    class Meta:
        model = RuleOperator
        fields = '__all__'

    def create(self, validated_data):
        return RuleOperator(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.value = validated_data.get('value', instance.value)
        instance.type = validated_data.get('type', instance.type)
        return instance


CONTAINS_STRING_OP = RuleOperator.create('contains', 'string')
MATCH_STRING_OP = RuleOperator.create('exact match', 'string')
CONTAINS_CAT_OP = RuleOperator.create('contains', 'categorical')
MATCH_CAT_OP = RuleOperator.create('exact match', 'categorical')
MATCH_NUMBER_OP = RuleOperator.create('exact match', 'number')

RuleOperatorType = Union[
    CONTAINS_STRING_OP,
    MATCH_STRING_OP,
    CONTAINS_CAT_OP,
    MATCH_CAT_OP,

    MATCH_NUMBER_OP
]


class RuleIF(ABC):

    @abstractmethod
    def get_clazz(self) -> str:
        pass

    @abstractmethod
    def evaluate(self, transaction: Transaction) -> bool:
        pass

    @abstractmethod
    def set_type(self, type: TransactionTypeEnum) -> None:
        pass


@dataclass
class Rule(RuleIF):
    FIELD_TYPE_CHOICES: ClassVar = [
        ('number', 'number'),
        ('string', 'string'),
        ('categorical', 'categorical'),
    ]

    MATCH_TYPE_CHOICES: ClassVar = [
        ('any of', 'any of'),
        ('all of', 'all of'),
    ]

    field: List[TransactionField]
    field_type: FieldType
    value: List[Any]
    value_match_type: RuleMatchTypes
    operator: RuleOperatorType
    clazz: Clazz
    type: TransactionTypeEnum

    def __post_init__(self):
        # check all the values of 'field' contain at most 1 period
        if not all(field.count('.') <= 1 for field in self.field):
            raise ValueError("Field must contain at most one period")

        if self.field_type == 'number' and not all(isinstance(val, (int, float)) for val in self.value):
            raise ValueError("All values must be numbers if the field_type is 'number'")
        if self.field_type in ['string', 'categorical'] and not all(isinstance(val, str) for val in self.value):
            raise ValueError("All values must be strings if the field_type is 'string' or 'categorical'")

        if self.field_type == 'number' and self.operator not in [MATCH_NUMBER_OP]:
            raise ValueError("Invalid operator for number field_type")
        if self.field_type in ['string', 'categorical'] and self.operator not in [CONTAINS_STRING_OP, MATCH_STRING_OP,
                                                                                  CONTAINS_CAT_OP, MATCH_CAT_OP]:
            raise ValueError(f"Encountered {self.operator}: Invalid operator for string or categorical field_type!")
        if self.operator in [MATCH_STRING_OP, MATCH_CAT_OP] and self.value_match_type == ALL_OF:
            raise ValueError("Value match type must be 'any of' if operator is 'exact match'")

    def _all_match(self, string_values_to_match: List[str], actual_value: str) -> bool:
        for string_value in string_values_to_match:
            if re.search(string_value.replace(' ', '\\s*'), actual_value, re.IGNORECASE):
                return True
        return False

    def _any_match(self, string_values_to_match: List[str], actual_value: str) -> bool:
        for string_value in string_values_to_match:
            if re.search(string_value.replace(' ', '\\s*'), actual_value, re.IGNORECASE):
                return True

        return False

    def evaluate_string(self, actual_value: str, string_values_to_match: List[str]) -> bool:
        if self.operator == CONTAINS_STRING_OP:
            if self.value_match_type == ANY_OF:
                return self._any_match(string_values_to_match, actual_value)
            elif self.value_match_type == ALL_OF:
                # return all(string_value.lower() in actual_value.lower() for string_value in string_values_to_match)
                return self._all_match(string_values_to_match, actual_value)

        elif self.operator == MATCH_STRING_OP:
            if self.value_match_type == ANY_OF:
                return self._any_match(string_values_to_match, actual_value)
            elif self.value_match_type == ALL_OF:
                return self._all_match(string_values_to_match, actual_value)
        else:
            raise ValueError(f"Unsupported operator {self.operator}")
        return False

    def _get_field_value(self, transaction: Transaction, field: TransactionField) -> Any:
        num_period = field.count('.')
        if num_period == 0:
            return getattr(transaction, field)
        elif num_period == 1:
            first_part, second_part = field.split('.')
            first_part_obj = getattr(transaction, first_part)
            return getattr(first_part_obj, second_part)
        else:
            raise ValueError("Field cannot have more than 1 '.'")

    def evaluate_field(self, transaction: Transaction, field: TransactionField) -> bool:
        actual_field_value = self._get_field_value(transaction, field)
        if actual_field_value is None:
            return False
        if self.field_type == 'number':
            if not isinstance(actual_field_value, (int, float)):
                raise ValueError(f"Field value is not a number: {actual_field_value}")
            if not all(isinstance(val, (int, float)) for val in self.value):
                raise ValueError("All values must be numbers")
            # Implement number evaluation logic here
            raise NotImplementedError("Number evaluation not implemented")
        elif self.field_type in ['string', 'categorical']:
            if not isinstance(actual_field_value, str):
                raise ValueError(f"Field value is not a string: {actual_field_value}")
            return self.evaluate_string(actual_field_value, self.value)
        return False

    def evaluate(self, transaction: Transaction) -> bool:
        return any(self.evaluate_field(transaction, field) for field in self.field)

    def set_type(self, type: TransactionTypeEnum) -> None:
        self.type = type

    def get_clazz(self) -> str:
        return self.clazz

    def __eq__(self, other):
        if not isinstance(other, Rule):
            return False
        return self.field == other.field and self.field_type == other.field_type and self.value == other.value and self.value_match_type == other.value_match_type and self.operator == other.operator and self.clazz == other.clazz and self.type == other.type


class RuleSerializer(serializers.Serializer):
    field = serializers.ListField(child=serializers.CharField())
    field_type = serializers.ChoiceField(choices=Rule.FIELD_TYPE_CHOICES)
    value = serializers.ListField(child=serializers.CharField())
    value_match_type = RuleMatchTypeSerializer()
    operator = RuleOperatorSerializer()
    clazz = serializers.CharField()
    type = EnumField(TransactionTypeEnum)

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data['value_match_type'] = RuleMatchType(**validated_data['value_match_type'])
        validated_data['operator'] = RuleOperator(**validated_data['operator'])
        return validated_data

    def create(self, validated_data):
        return Rule(**validated_data)

    def update(self, instance, validated_data):
        instance.field = validated_data.get('field', instance.field)
        instance.field_type = validated_data.get('field_type', instance.field_type)
        instance.value = validated_data.get('value', instance.value)
        instance.value_match_type = validated_data.get('value_match_type', instance.value_match_type)
        instance.operator = validated_data.get('operator', instance.operator)
        instance.clazz = validated_data.get('clazz', instance.clazz)
        instance.type = validated_data.get('type', instance.type)
        return instance


@dataclass
class RuleSet(RuleIF):
    condition: Condition
    rules: List[Union[Rule, 'RuleSet']]
    is_child: bool
    clazz: str
    type: TransactionTypeEnum

    def __post_init__(self) -> None:
        if isinstance(self.type, str):
            self.type = TransactionTypeEnum.from_value(self.type)

    def evaluate(self, transaction: Transaction):
        if not self.rules:
            return False
        if self.condition == 'AND':
            return all(rule.evaluate(transaction) for rule in self.rules)
        elif self.condition == 'OR':
            return any(rule.evaluate(transaction) for rule in self.rules)
        return False

    def set_type(self, type):
        self.type = type
        for rule in self.rules:
            rule.set_type(type)

    def get_clazz(self) -> str:
        return self.clazz

    def __eq__(self, other):
        if not isinstance(other, RuleSet):
            return False
        return self.condition == other.condition and self.rules == other.rules and self.is_child == other.is_child


class RuleSetSerializer0(Serializer):
    condition = serializers.ChoiceField(choices=['AND', 'OR'])
    rules = serializers.ListField()  # We'll handle this in the extension.
    is_child = serializers.BooleanField()
    clazz = serializers.CharField()
    type = EnumField(TransactionTypeEnum)


class RuleSetSerializer(serializers.Serializer):
    condition = serializers.ChoiceField(choices=['AND', 'OR'])
    rules = serializers.SerializerMethodField()
    is_child = serializers.BooleanField()
    clazz = serializers.CharField()
    type = EnumField(TransactionTypeEnum)
    def to_internal_value(self, data):
        # Custom deserialization logic
        rules = []
        for rule_data in data.get('rules', []):
            if 'condition' in rule_data:
                rules.append(RuleSetSerializer().to_internal_value(rule_data))
            else:
                rules.append(RuleSerializer().to_internal_value(rule_data))
        rules_with_rule_set_objects = []
        for rule in rules:
            if isinstance(rule, Rule):
                rules_with_rule_set_objects.append(rule)
            elif isinstance(rule, RuleSet):
                rules_with_rule_set_objects.append(rule)
            elif isinstance(rule, dict) and rule['clazz'] == 'Rule':
                rules_with_rule_set_objects.append(Rule(**rule))

            elif isinstance(rule, dict) and rule['clazz'] == 'RuleSet':
                rules_with_rule_set_objects.append(RuleSet(**rule))

            else:

                raise ValueError(f"Unsupported type: {type(rule)}")
        validated_data = {
            'condition': data.get('condition'),
            'rules': rules_with_rule_set_objects,
            'is_child': data.get('is_child'),
            'clazz': data.get('clazz'),
            'type': data.get('type'),
        }
        return validated_data



    def get_rules(self, obj):
        def serialize_rule_or_ruleset(rule_or_ruleset):
            if isinstance(rule_or_ruleset, Rule):
                data = RuleSerializer(rule_or_ruleset).data
                return data
            elif isinstance(rule_or_ruleset, RuleSet):
                data =RuleSetSerializer(rule_or_ruleset).data
                return data
            else:
                raise TypeError(f"Unsupported type: {type(rule_or_ruleset)}")

        # Assume `obj.rules` is a list of Rule or RuleSet objects
        result = []
        for child in obj.rules:
            serialized = serialize_rule_or_ruleset(child)
            result.append(serialized)
        return result

    def create(self, validated_data):
        rules = []
        for rule_data in validated_data['rules']:
            if isinstance(rule_data, dict) and 'condition' in rule_data:
                rules.append(RuleSetSerializer().create(rule_data))
            else:
                rules.append(RuleSerializer().create(rule_data))

        return RuleSet(
            condition=validated_data['condition'],
            rules=rules,
            is_child=validated_data['is_child'],
            clazz=validated_data['clazz'],
            type=validated_data['type'],
        )

    def update(self, instance, validated_data):
        instance.condition = validated_data.get('condition', instance.condition)
        instance.rules = []
        for rule_data in validated_data['rules']:
            if isinstance(rule_data, dict) and 'condition' in rule_data:
                instance.rules.append(RuleSetSerializer().update(instance, rule_data))
            else:
                instance.rules.append(RuleSerializer().update(instance, rule_data))
        instance.is_child = validated_data.get('is_child', instance.is_child)
        instance.clazz = validated_data.get('clazz', instance.clazz)
        instance.type = validated_data.get('type', instance.type)
        return instance


class RuleSetSerializerExtension(OpenApiSerializerExtension):
    target_class = 'pybackend.rules.RuleSetSerializer'
    match_subclasses = True

    def map_serializer(self, auto_schema, direction):
        original = auto_schema._map_serializer(self.target_class, direction, bypass_extensions=True)
        rules = {
            "type": "array",
            "items": {
                "oneOf": [
                    {"$ref": "#/components/schemas/RuleSet"},
                    {"$ref": "#/components/schemas/Rule"}
                ]
            },
            "readOnly": True
        }
        original['properties']['rules'] = rules
        return original


class RuleSetWrapper(models.Model):
    id = models.AutoField(primary_key=True)
    category = models.OneToOneField(Category, on_delete=models.CASCADE)
    rule_set = models.TextField()  # Store as JSON string
    users = models.ManyToManyField(CustomUser)
    objects = RuleSetWrapperManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if isinstance(self.rule_set, str):
            self.rule_set = self.get_rule_set()

    def set_rule_set(self, rule_set: RuleSet):
        if not isinstance(rule_set, RuleSet):
            raise ValueError(f"Invalid rule_set type: {type(rule_set)}")
        self.rule_set = json.dumps(RuleSetSerializer(rule_set).data)
    def get_rule_set(self):
        if isinstance(self.rule_set, str):
            serializer = RuleSetSerializer(data=json.loads(self.rule_set))
            if serializer.is_valid(raise_exception=True):
                return RuleSet(**serializer.validated_data)
        elif isinstance(self.rule_set, dict):
            serializer = RuleSetSerializer(data=self.rule_set)
            if serializer.is_valid(raise_exception=True):
                return RuleSet(**serializer.validated_data)
        elif isinstance(self.rule_set, RuleSet):
            return self.rule_set
        else:
            raise ValueError(f"Invalid rule_set type: {type(self.rule_set)}")

    def save(self, *args, **kwargs):
        if not isinstance(self.rule_set, str):
            self.set_rule_set(self.rule_set)
        super().save(*args, **kwargs)

class SimpleUserSerializer(serializers.Serializer):
    username = serializers.CharField()
    class Meta:
        model = CustomUser
        fields = ['username']

    def create(self, validated_data):
        user = CustomUser.objects.get(username=validated_data['username'])
        return user

class RuleSetWrapperSerializer(DeserializeInstanceMixin):
    id = serializers.IntegerField(read_only=True)
    category = SimpleCategorySerializer()
    rule_set = serializers.SerializerMethodField()
    users = SimpleUserSerializer(many=True)

    class Meta:
        model = RuleSetWrapper
        fields = '__all__'

    def to_internal_value(self, data):

        rule_set = RuleSet(**RuleSetSerializer().to_internal_value(data['rule_set']))
        category = SimpleCategorySerializer().create(data['category'])
        users = [SimpleUserSerializer().create(user) for user in data['users']]
        return {
            'id': data.get('id'),
            'category': category,
            'rule_set': rule_set,
            'users': users
        }

    def create(self, validated_data):

        return RuleSetWrapper(**validated_data)



    def update(self, instance, validated_data):
        if not 'rule_set' in validated_data:
            return instance
        rule_set = validated_data.pop('rule_set')
        if isinstance(rule_set, RuleSet):
            instance.rule_set = json.dumps(RuleSetSerializer(rule_set).data)
        elif isinstance(rule_set, Dict):
            instance.rule_set = json.dumps(RuleSetSerializer(rule_set))
        elif isinstance(rule_set, str):
            instance.rule_set = rule_set
        else:
            raise ValueError(f"Invalid rule_set type: {type(rule_set)}")
        instance.save()
        return instance
    @extend_schema_field(RuleSetSerializer())
    def get_rule_set(self, obj):
        rule_set = obj.rule_set
        if isinstance(rule_set, str):
            return json.loads(rule_set)
        return RuleSetSerializer(rule_set).data

class RuleSetWrappersPostOrderTraverser:
    def __init__(self, expenses_category_tree: CategoryTree, revenue_category_tree: CategoryTree,
                 rule_set_wrappers: List[RuleSetWrapper]):
        self.expenses_category_tree = self._category_tree_to_nx_digraph(expenses_category_tree)
        self.revenue_category_tree = self._category_tree_to_nx_digraph(revenue_category_tree)
        self.rules_by_category = {wrapper.category: wrapper for wrapper in rule_set_wrappers}
        self.current_transaction: Optional[Transaction] = None
        self.current_category: Optional[Category] = None
        self.counter = defaultdict(int)

    def _category_tree_to_nx_digraph(self, category_tree: CategoryTree) -> nx.DiGraph:
        graph = nx.DiGraph()

        def add_category_to_graph(category: Category):
            graph.add_node(category)
            for child in category.cached_children:
                graph.add_edge(category, child)
                add_category_to_graph(child)

        add_category_to_graph(category_tree.root)
        return graph

    def set_current_transaction(self, transaction: Transaction):
        self.current_transaction = transaction

    def traverse(self) -> Optional[Category]:
        if self.current_transaction is None:
            raise ValueError("Transaction must be set before traversing!")

        root = self.get_root_category()
        categories_in_post_order = list(nx.dfs_postorder_nodes(self.get_category_tree(), root))

        for category in categories_in_post_order:
            self.current_category = category
            if self.rule_set_matches(category):
                if self.current_category is None:
                    raise ValueError("Category must be set after traversing!")
                self.current_transaction.category = self.current_category
                return self.current_category

        return None

    def get_root_category(self) -> Category:
        if self.current_transaction.get_transaction_type == 'EXPENSES':
            return [n for n, d in self.expenses_category_tree.in_degree() if d == 0][0]
        else:
            return [n for n, d in self.revenue_category_tree.in_degree() if d == 0][0]

    def get_category_tree(self) -> nx.DiGraph:
        if self.current_transaction.get_transaction_type == 'EXPENSES':
            return self.expenses_category_tree
        else:
            return self.revenue_category_tree

    def rule_set_matches(self, category: 'Category') -> bool:
        rule_set_wrapper = self.rules_by_category.get(category)
        if rule_set_wrapper is None:
            return False
        return rule_set_wrapper.rule_set.evaluate(self.current_transaction)
