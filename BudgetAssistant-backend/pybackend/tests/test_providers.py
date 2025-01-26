import importlib.resources as pkg_resources
from typing import List, Set

from django.test import TestCase
from model_bakery import baker

from pybackend.commons import TransactionTypeEnum
from pybackend.models import BankAccount, BudgetTree, BudgetTreeNode, Category, CategoryTree
from pybackend.providers import BudgetTreeProvider, CategoryTreeInserter, CategoryTreeProvider


def load_expenses_categories_from_file() -> List[str]:
    with pkg_resources.open_text('pybackend.resources', 'categories-expenses.txt') as file:
        lines = file.read().split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        lines.append(Category.NO_CATEGORY_NAME)
        lines.append(Category.DUMMY_CATEGORY_NAME)
        return lines

class CategoryTreeInserterTests(TestCase):

    def setUp(self):
        self.inserter = CategoryTreeInserter()

    def test_run_creates_category_tree_with_root(self):
        tree = self.inserter.run(TransactionTypeEnum.EXPENSES)
        self.assertIsNotNone(tree)
        self.assertEqual(tree.root.name, Category.ROOT_NAME)
        self.assertTrue(tree.root.is_root)


    def test_run_creates_no_category_and_dummy_category(self):
        tree = self.inserter.run(TransactionTypeEnum.EXPENSES)
        no_category =baker.make(Category, name=Category.NO_CATEGORY_NAME, qualified_name=Category.NO_CATEGORY_NAME)
        dummy_category =baker.make( Category, name=Category.DUMMY_CATEGORY_NAME, qualified_name=Category.DUMMY_CATEGORY_NAME)
        self.assertIn(no_category, tree.root.cached_children)
        self.assertIn(dummy_category, tree.root.cached_children)

    def test_run_invalid_category_tree_type_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.inserter.run(TransactionTypeEnum.BOTH)


    def test_tree_expenses_tree_is_correctly_inserted(self):
        expected_qualified_names = """
        belastingen
        belastingen#KI
        belastingen#verkeersbelasting
        belastingen#boekhouder
        belastingen#personenbelasting
        belastingen#provinciebelasting
        belastingen#gemeentebelasting
        energie
        energie#gas & elektriciteit
        energie#water
        bankkosten
        leningen
        leningen#woonlening
        verzekeringen
        verzekeringen#brand- en familiale verzekering
        verzekeringen#schuldsaldo
        verzekeringen#autoverzekering
        verzekeringen#hospitalisatieverzekering
        auto & vervoer
        auto & vervoer#autoverzekering
        auto & vervoer#benzine
        auto & vervoer#parkeren
        auto & vervoer#onderhoud & herstelling
        auto & vervoer#trein
        kinderen
        kinderen#kinderopvang
        kinderen#school
        kinderen#school#boeken/materiaal
        kinderen#school#schoolreis
        kinderen#school#middagmaal
        kinderen#kleding
        kinderen#uitrusting
        kinderen#speelgoed
        kledij & verzorging
        kledij & verzorging#accessoires
        kledij & verzorging#kapper
        kledij & verzorging#schoenen
        kledij & verzorging#kleren
        wonen
        wonen#meubelen & accessoires
        wonen#poetsdienst
        wonen#tuin
        wonen#renovaties
        wonen#loodgieter
        wonen#chauffage
        wonen#keuken
        wonen#electro
        huishouden
        huishouden#boodschappen
        huishouden#boodschappen#bakker
        huishouden#boodschappen#slager
        huishouden#boodschappen#supermarkt
        huishouden#boodschappen#supermarkt#colruyt
        huishouden#lunch werk
        medisch
        medisch#dokter
        medisch#kinesist
        medisch#apotheek
        medisch#mutualiteit
        medisch#ziekenhuis
        medisch#dierenarts
        medisch#tandarts
        telecom
        telecom#internet & tv
        telecom#telefonie
        vrije tijd
        vrije tijd#restaurant
        vrije tijd#café
        vrije tijd#uitgaan
        vrije tijd#hobby
        vrije tijd#reizen
        giften
        giften#cadeau's
        vakbond
        sparen
        sparen#pensioensparen
        sparen#algemeen
        cash geldopname
        kredietkaart
        gemeenschappelijke kosten
        webshops"""
        expected_qualified_names = {name.strip() for name in expected_qualified_names.split('\n') if name.strip()}
        expected_qualified_names.add(Category.NO_CATEGORY_NAME)
        expected_qualified_names.add(Category.DUMMY_CATEGORY_NAME)

        tree = self.inserter.run(TransactionTypeEnum.EXPENSES)
        root = Category.objects.find_by_qualified_name_with_children(Category.ROOT_NAME)
        all_descendants = []
        def handle_category(category: Category):
            qualified_name = category.qualified_name
            all_descendants.append(qualified_name)
            for child in category.cached_children:
                handle_category(child)

        for child in root.cached_children:
            handle_category(child)

        actual_qualified_names = set(all_descendants)
        self.assertSetEqual(expected_qualified_names, actual_qualified_names)



class CategoryTreeProviderTests(TestCase):

    def setUp(self):
        self.provider = CategoryTreeProvider()

    def test_provide_creates_category_tree_with_root(self):
        tree = self.provider.provide(TransactionTypeEnum.EXPENSES)
        self.assertIsNotNone(tree)
        self.assertEqual(tree.root.name, Category.ROOT_NAME)
        self.assertTrue(tree.root.is_root)
        # check
        expected_categories = load_expenses_categories_from_file()
        actual_categories = []
        def get_descendants(category: Category):

            actual_categories.append(category.name)
            for child in category.cached_children:
                get_descendants(child)

        for child in tree.root.cached_children:
            get_descendants(child)

        actual_categories.sort()
        expected_categories.sort()
        self.assertSetEqual(set(expected_categories), set(actual_categories))
        self.assertEqual(len(expected_categories), len(actual_categories))

    def test_provide_creates_no_category_and_dummy_category(self):
        tree = self.provider.provide(TransactionTypeEnum.EXPENSES)
        no_category = Category.objects.get(name=Category.NO_CATEGORY_NAME)
        dummy_category = Category.objects.get(name=Category.DUMMY_CATEGORY_NAME)
        self.assertIn(no_category, tree.root.cached_children)
        self.assertIn(dummy_category, tree.root.cached_children)

    def test_provide_invalid_category_tree_type_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.provider.provide("INVALID_TYPE")



class BudgetTreeProviderTests(TestCase):

    def setUp(self):
        self.expenses_category_tree = CategoryTree.objects.create(
            root=Category.objects.create(name=Category.ROOT_NAME, is_root=True, type=TransactionTypeEnum.EXPENSES),
            type=TransactionTypeEnum.EXPENSES
        )
        self.provider = BudgetTreeProvider()
        self.bank_account = BankAccount.objects.create(account_number="123456789")

    def test_provide_creates_budget_tree_with_root(self):
        budget_tree = self.provider.provide(self.bank_account)
        self.assertIsNotNone(budget_tree)
        self.assertEqual(budget_tree.root.category.name, Category.ROOT_NAME)
        self.assertTrue(budget_tree.root.category.is_root)
        expenses_tree = CategoryTreeProvider().provide(TransactionTypeEnum.EXPENSES)
        #create a dictionary of all categories in the expenses tree. the key is the qualified_name, the value is the category object
        categories = {}
        def get_categories(category: Category):
            categories[category.qualified_name] = category
            for child in category.cached_children:
                get_categories(child)
        get_categories(expenses_tree.root)

        #create a dict of all BudgetTreeNodes in the budget_tree. the key is the qualified_name, the value is the BudgetTreeNode object
        budget_tree_nodes = {}
        def get_budget_tree_nodes(node: BudgetTreeNode):
            budget_tree_nodes[node.category.qualified_name] = node
            for child in node.cached_children:
                get_budget_tree_nodes(child)
        get_budget_tree_nodes(budget_tree.root)
        #check that both dictionaries have more than 0 keys
        self.assertGreater(len(categories), 0)
        self.assertGreater(len(budget_tree_nodes), 0)
        #check if all categories in the expenses tree are present in the budget_tree by comparing the keys
        self.assertSetEqual(set(categories.keys()), set(budget_tree_nodes.keys()))




    def test_provide_creates_budget_tree_with_children(self):
        child_category = baker.make(Category, name="ChildCategory", qualified_name="ChildCategory", parent=self.expenses_category_tree.root,
                                                 type=TransactionTypeEnum.EXPENSES)
        self.expenses_category_tree.root.add_child(child_category)
        budget_tree = self.provider.provide(self.bank_account)
        children_ = [node.category for node in budget_tree.root.cached_children]
        self.assertIn(child_category, children_)

    def test_provide_existing_budget_tree(self):
        existing_budget_tree = BudgetTree.objects.create(bank_account=self.bank_account,
                                                         root=BudgetTreeNode.objects.create(
                                                             category=self.expenses_category_tree.root, amount=-1))
        budget_tree = self.provider.provide(self.bank_account)
        self.assertEqual(budget_tree, existing_budget_tree)

    def test_provide_invalid_category_tree_type_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.provider.provide("INVALID_TYPE")
