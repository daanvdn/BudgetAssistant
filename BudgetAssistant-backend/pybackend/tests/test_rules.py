import itertools
import itertools
import random
from abc import ABC, abstractmethod
from typing import List, Tuple, Union

from django.test import TestCase
from faker import Faker
from model_bakery import baker
from parameterized import parameterized

from pybackend.models import Category, CustomUser, Transaction
from pybackend.rules import ALL_OF, ANY_OF, CONTAINS_STRING_OP, MATCH_STRING_OP, Rule, \
    RuleMatchType, RuleOperator, RuleSerializer, RuleSet, RuleSetSerializer, RuleSetWrapper, RuleSetWrapperSerializer, \
    TransactionField
from pybackend.tests.utils import RuleSetFactory, StringRuleFactory, create_random_rule_set

faker = Faker()


class Attribute(ABC):

    @abstractmethod
    def is_nested_attribute(self) -> bool:
        pass

    @abstractmethod
    def set_attribute(self, target_string: str, transaction: Transaction, rule: Rule) -> Transaction:
        pass

    @staticmethod
    def create(attribute_name: TransactionField) -> 'Attribute':
        if not isinstance(attribute_name, str):
            raise ValueError("Attribute name must be a string")
        if '.' in attribute_name:
            return NestedAttribute(attribute_name)
        return SimpleAttribute(attribute_name)


class SimpleAttribute(Attribute):

    def __init__(self, attribute_name: TransactionField):
        self.attribute_name = attribute_name

    def is_nested_attribute(self) -> bool:
        return False

    def set_attribute(self, target_string: str, transaction: Transaction, rule: Rule):
        setattr(transaction, self.attribute_name, target_string)
        if rule.value:
            if not isinstance(rule.value, list):
                raise ValueError("Rule value must be a list")
        else:
            rule.value = []
        rule.value.append(target_string)
        if rule.field:
            if not isinstance(rule.field, list):
                raise ValueError("Rule field must be a list")
        else:
            rule.field = []
        rule.field.append(self.attribute_name)

        return transaction


class NestedAttribute(Attribute):

    def __init__(self, attribute_name: str):
        if '.' not in attribute_name:
            raise ValueError("Field must contain '.'")
        if attribute_name.count('.') > 1:
            raise ValueError("Field cannot have more than 1 '.'")
        self.attribute_name = attribute_name

    def is_nested_attribute(self) -> bool:
        return True

    def set_attribute(self, target_string: str, transaction: Transaction, rule: Rule):
        first_part, second_part = self.attribute_name.split('.')
        first_part_obj = getattr(transaction, first_part)
        setattr(first_part_obj, second_part, target_string)
        setattr(transaction, first_part, first_part_obj)
        if rule.value:
            if not isinstance(rule.value, list):
                raise ValueError("Rule value must be a list")
            else:
                rule.value = []
        rule.value.append(target_string)
        if rule.field:
            if not isinstance(rule.field, list):
                raise ValueError("Rule field must be a list")
            else:
                rule.field = []
        rule.field.append(self.attribute_name)
        return transaction


class RuleAndTransactionPreparer:

    def __init__(self, transaction: Transaction, rule: Rule):
        self.rule = rule
        self.operator = rule.operator
        self.fields = rule.field
        self.value_match_type = rule.value_match_type
        self.target_strings = rule.value
        self.transaction = transaction

    def _select_fields(self) -> Union[TransactionField, List[TransactionField]]:
        return random.choice(self.fields)

    def _select_target_strings(self) -> Union[str, List[str]]:
        if self.value_match_type == ALL_OF:
            return self.target_strings.copy()
        elif self.value_match_type == ANY_OF:
            return random.choice(self.target_strings)
        else:
            raise ValueError("Value match type not supported")

    def _create_fake_text(self, selected_target_string: str) -> str:
        random.seed(0)

        if self.operator == CONTAINS_STRING_OP:
            fake_text = ' '.join(faker.words(nb=random.randint(1, 10)))

            position = random.randint(0, len(fake_text))
            return fake_text[:position] + selected_target_string + fake_text[position:]
        elif self.operator == MATCH_STRING_OP:
            return selected_target_string
        else:
            raise ValueError("Operator not supported")

    def run(self) -> Tuple[Rule, Transaction]:
        self.selected_fields = self._select_fields()
        self.selected_target_strings = self._select_target_strings()
        if isinstance(self.selected_fields, str):
            if isinstance(self.selected_target_strings, str):
                fake_text = self._create_fake_text(self.selected_target_strings)
                attribute = Attribute.create(self.selected_fields)
                return self.rule, attribute.set_attribute(fake_text, self.transaction, self.rule)
            elif isinstance(self.selected_target_strings, list):
                fake_texts = []
                for target_string in self.selected_target_strings:
                    fake_texts.append(self._create_fake_text(target_string))
                attribute = Attribute.create(self.selected_fields)
                self.transaction = attribute.set_attribute(' '.join(fake_texts), self.transaction, self.rule)
                return self.rule, self.transaction
            else:
                raise ValueError("Field type not supported")
        elif isinstance(self.selected_fields, list):
            for field in self.selected_fields:
                if isinstance(self.selected_target_strings, str):
                    fake_text = self._create_fake_text(self.selected_target_strings)
                    attribute = Attribute.create(field)
                    self.transaction = attribute.set_attribute(fake_text, self.transaction, self.rule)
                elif isinstance(self.selected_target_strings, list):
                    for target_string in self.selected_target_strings:
                        fake_text = self._create_fake_text(target_string)
                        attribute = Attribute.create(field)
                        self.transaction = attribute.set_attribute(fake_text, self.transaction, self.rule)
                else:
                    raise ValueError("Field type not supported")
            return self.rule, self.transaction
        else:
            raise ValueError("Field type not supported")


class CreateTestCasesStringMixin():
    def create_test_cases_string(self, operator: RuleOperator, value_match_type: RuleMatchType):
        fake = Faker()
        random.seed(0)
        cases = []
        for i in range(100):
            value_list_length = random.randint(1, 5)
            # create a list of random strings of length value_list_length. Use faker to generate random words
            value_list = [" ".join(fake.words(nb=random.randint(1, 10))) for _ in range(value_list_length)]

            rule = StringRuleFactory.build(value=value_list, operator=operator, value_match_type=value_match_type)
            transaction = baker.make(Transaction)
            cases.append({'rule': rule, 'transaction': transaction})
        return cases


class RuleTests(TestCase, CreateTestCasesStringMixin):

    def test_evaluate_string_contains_any_of(self):
        for item in self.create_test_cases_string(CONTAINS_STRING_OP, ANY_OF):
            rule = item['rule']
            transaction = item['transaction']
            rule, transaction = RuleAndTransactionPreparer(transaction, rule).run()
            self.assertTrue(rule.evaluate(transaction))

    def test_evaluate_string_contains_all_of(self):
        data = self.create_test_cases_string(CONTAINS_STRING_OP, ALL_OF)
        for item in data:
            rule = item['rule']
            transaction = item['transaction']
            rule, transaction = RuleAndTransactionPreparer(transaction, rule).run()
            evaluate = rule.evaluate(transaction)
            self.assertTrue(evaluate)

    def test_evaluate_string_exact_match_any_of(self):
        for item in self.create_test_cases_string(MATCH_STRING_OP, ANY_OF):
            rule = item['rule']
            transaction = item['transaction']
            rule, transaction = RuleAndTransactionPreparer(transaction, rule).run()
            self.assertTrue(rule.evaluate(transaction))

    def test_evaluate_string_exact_match_all_of_fails(self):
        with self.assertRaises(ValueError):
            self.create_test_cases_string(MATCH_STRING_OP, ALL_OF)


class RuleSetWrapperTest(TestCase):
    maxDiff = None

    def test_save_rule_set_wrapper(self):
        rule_set = create_random_rule_set()
        user = baker.make(CustomUser, username='testuser', password='password')
        category = baker.make(Category, name='category', type='EXPENSES')
        expected = baker.make(RuleSetWrapper, category=category, users=[user], rule_set=rule_set)
        actual = RuleSetWrapper.objects.get(id=expected.id)
        self.assertTrue(actual)
        self.assertIsNotNone(actual)
        self.assertIsNotNone(actual.rule_set)
        self.assertIsInstance(actual.get_rule_set(), RuleSet)
        self.assertEqual(actual.get_rule_set(), rule_set)
        self.assertEqual(actual.category, category)
        self.assertEqual(actual.users.first(), user)
        self.assertEqual(actual, expected)

    def test_update_rule_set_wrapper(self):
        rule_set = create_random_rule_set()
        user = baker.make(CustomUser, username='testuser', password='password')
        category = baker.make(Category, name='category', type='EXPENSES')
        expected = baker.make(RuleSetWrapper, category=category, users=[user], rule_set=rule_set)
        self.assertIsInstance(expected.get_rule_set(), RuleSet)
        actual = RuleSetWrapper.objects.get(id=expected.id)
        self.assertTrue(actual)
        self.assertIsNotNone(actual)
        actual_rule_set = actual.get_rule_set()
        self.assertIsNotNone(actual_rule_set)
        self.assertIsInstance(actual_rule_set, RuleSet)
        self.assertEqual(actual_rule_set, expected.get_rule_set())
        self.assertEqual(actual.category, category)
        self.assertEqual(actual.users.first(), user)
        self.assertEqual(actual, expected)
        new_rule_set = create_random_rule_set()
        self.assertNotEqual(new_rule_set, rule_set)
        expected.rule_set = new_rule_set
        expected.save()
        actual = RuleSetWrapper.objects.get(id=expected.id)
        self.assertTrue(actual)
        self.assertIsNotNone(actual)
        actual_rule_set = actual.get_rule_set()
        self.assertIsNotNone(actual_rule_set)
        self.assertIsInstance(actual_rule_set, RuleSet)
        self.assertEqual(actual_rule_set, expected.get_rule_set())
        self.assertEqual(actual.category, category)
        self.assertEqual(actual.users.first(), user)
        self.assertEqual(actual, expected)


class RuleSerializerTest(TestCase, CreateTestCasesStringMixin):

    @parameterized.expand(list(itertools.product([CONTAINS_STRING_OP], [ALL_OF, ANY_OF])))
    def test_serialize_deserialize(self, rule_operator: RuleOperator, value_match_type: RuleMatchType):
        for case in self.create_test_cases_string(rule_operator, value_match_type):
            rule: Rule = case['rule']
            serializer = RuleSerializer(rule)
            serialized_data = serializer.data
            deserialized = RuleSerializer(data=serialized_data)
            if deserialized.is_valid():
                deserialized_data = deserialized.validated_data
                deserialized_obj = Rule(**deserialized_data)
                self.assertEqual(rule, deserialized_obj)
            else:
                self.fail(f"Deserialization failed: {deserialized.errors}")


def create_random_rule_set_2() -> RuleSet:
    def _create_rule() -> Rule:
        return StringRuleFactory.build()

    def _create_rule_set() -> RuleSet:
        rule_set = RuleSetFactory.build()
        rule_set.rules = [_create_rule() for _ in range(5)]
        return rule_set

    depth = 3

    # create a RuleSet object whose rules field is 10 levels deep. Each level has 5 Rule object or 5 RuleSet objects. Use _create_rule and _create_rule_set functions to create the Rule objects and RuleSet objects respectively

    def _create_rule_set_recursive(current_depth: int) -> RuleSet:
        if current_depth == depth:
            return _create_rule_set()
        rule_set = RuleSetFactory.build()
        rule_set.rules = [_create_rule_set_recursive(current_depth + 1) for _ in range(5)]
        return rule_set

    return _create_rule_set_recursive(0)


class RuleSetSerializerTest(TestCase):
    @parameterized.expand([create_random_rule_set_2(),create_random_rule_set()])
    def test_serialize_deserialize(self, rule_set: RuleSet):
        serialized_data = RuleSetSerializer(rule_set).data
        serializer = RuleSetSerializer(data=serialized_data)
        if serializer.is_valid(raise_exception=True):
            deserialized_obj = RuleSet(**serializer.validated_data)
            self.assertEqual(rule_set, deserialized_obj)
        else:
            self.fail(f"Deserialization failed: {serializer.errors}")


class RuleSetWrapperSerializerTest(TestCase):

    def setUp(self):
        #clear database
        RuleSetWrapper.objects.all().delete()
        CustomUser.objects.all().delete()
        Category.objects.all().delete()
        self.user = CustomUser.objects.create_user(username="testuser", password="password123")
        self.categories = baker.make(Category, type='EXPENSES', _quantity=5)

    @parameterized.expand([create_random_rule_set_2(),create_random_rule_set()])
    def test(self, rule_set:RuleSet):
        expected: RuleSetWrapper = baker.make(RuleSetWrapper, rule_set=rule_set, users=[self.user], category=self.categories[0])
        serialized = RuleSetWrapperSerializer(expected).data
        serializer = RuleSetWrapperSerializer(data=serialized)
        if serializer.is_valid():
            validated_data = serializer.validated_data
            users = validated_data.pop('users')
            actual = RuleSetWrapper(**validated_data)
            actual.users.set(users)
            self.assertEqual(expected, actual)


