import importlib.resources as pkg_resources
import re
from typing import Dict, List

from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction

from pybackend.models import BudgetTree, BudgetTreeNode, Category, CategoryTree
from pybackend.commons import TransactionTypeEnum


class CategoryTreeInserter0:
    LEADING_TABS = re.compile(r'^\t+')

    def __init__(self):
        pass

    def get_nr_of_leading_tabs(self, line):
        matcher = self.LEADING_TABS.match(line)
        if matcher:
            return len(matcher.group())
        return 0

    def handle_item(self, parent, lines, current_index, all_categories, type):
        current = lines[current_index]
        current_category = Category(name=current.strip(), parent=parent, is_root=False, type=type)
        current_category.save()
        parent.add_child(current_category)
        parent.save()
        all_categories.append(current_category)
        nr_of_leading_tabs = self.get_nr_of_leading_tabs(current)
        last_consumed_index = current_index
        for i in range(current_index + 1, len(lines)):
            next_nr_of_leading_tabs = self.get_nr_of_leading_tabs(lines[i])
            if next_nr_of_leading_tabs == nr_of_leading_tabs + 1:
                last_consumed_index = i
                self.handle_item(current_category, lines, i, all_categories, type)
            elif next_nr_of_leading_tabs == nr_of_leading_tabs or next_nr_of_leading_tabs == 0:
                break
        return last_consumed_index

    @transaction.atomic
    def run(self, type):
        if type == TransactionTypeEnum.EXPENSES:
            resource = 'categories-expenses.txt'
        elif type == TransactionTypeEnum.REVENUE:
            resource = 'categories-revenue.txt'
        else:
            raise ValueError("Invalid category tree type")

        with pkg_resources.open_text('pybackend.resources', resource) as file:
            lines = file.read().split('\n')

        root = Category(name=Category.ROOT_NAME, parent=None, is_root=True, type=type)
        root.save()
        all_categories = [root]

        for i in range(len(lines)):
            i = self.handle_item(root, lines, i, all_categories, type)

        no_category = Category(name=Category.NO_CATEGORY_NAME, parent=root, is_root=False, type=type)
        no_category.save()
        root.add_child(no_category)

        dummy_category = Category(name=Category.DUMMY_CATEGORY_NAME, parent=root, is_root=False, type=type)
        dummy_category.save()
        root.add_child(dummy_category)

        tree = CategoryTree(root=root, type=type)
        tree.save()
        return tree

class CategoryTreeInserter:
    LEADING_TABS = re.compile(r'^\t+')

    def __init__(self):
        pass


    def _parse_lines(self, lines):
        LEADING_TABS = re.compile(r'^\t+')
        result = []
        ancestors = []

        for line in lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue

            # Determine the number of leading tabs
            leading_tabs = LEADING_TABS.match(line)
            level = len(leading_tabs.group()) if leading_tabs else 0

            # Adjust the ancestors list to the current level
            if level < len(ancestors):
                ancestors = ancestors[:level]
            elif level > len(ancestors):
                ancestors.append(ancestors[-1])

            # Add the current category to the ancestors list
            if level == 0:
                ancestors = [stripped_line]
            else:
                ancestors.append(stripped_line)

            # Construct the full path
            full_path = '#'.join(ancestors)
            result.append(full_path)
        #sort lines ascending
        result.sort()
        return result

    def _insert_lines(self, lines:List[str], root: Category, type: TransactionTypeEnum):
        inserted_categories: Dict[str, Category] =dict()
        parsed_lines = self._parse_lines(lines)
        for qualified_name in parsed_lines:
            qualified_name_parts = qualified_name.split('#')
            parent = root
            for i in range(len(qualified_name_parts)):
                #get parts 0 till i
                partial_qualified_name = '#'.join(qualified_name_parts[:i+1])
                #check if category exists
                if partial_qualified_name in inserted_categories:
                    parent = inserted_categories[partial_qualified_name]

                else:
                    category = Category(name=qualified_name_parts[i], parent=parent, is_root=False, type=type, qualified_name=partial_qualified_name)
                    category.save()
                    inserted_categories[partial_qualified_name] = category


    @transaction.atomic
    def run(self, type):
        if type == TransactionTypeEnum.EXPENSES:
            resource = 'categories-expenses.txt'
        elif type == TransactionTypeEnum.REVENUE:
            resource = 'categories-revenue.txt'
        else:
            raise ValueError("Invalid category tree type")

        with pkg_resources.open_text('pybackend.resources', resource) as file:
            lines = file.read().split('\n')

        root = Category(name=Category.ROOT_NAME, parent=None, is_root=True, type=type, qualified_name=Category.ROOT_NAME)
        root.save()
        no_category = Category(name=Category.NO_CATEGORY_NAME, parent=root, is_root=False, type=type, qualified_name=Category.NO_CATEGORY_NAME)
        no_category.save()

        dummy_category = Category(name=Category.DUMMY_CATEGORY_NAME, parent=root, is_root=False, type=type, qualified_name=Category.DUMMY_CATEGORY_NAME)
        dummy_category.save()
        self._insert_lines(lines, root, type)

        tree = CategoryTree(root=root, type=type.name)
        tree.save()
        return tree


class CategoryTreeProvider:
    LEADING_TABS = re.compile(r'^\t+')

    def __init__(self):
        pass


    @transaction.atomic
    def provide(self, type: TransactionTypeEnum):
        category_tree = CategoryTree.objects.find_category_tree_by_type(type)
        if category_tree:
            return category_tree
        return CategoryTreeInserter().run(type)

class BudgetTreeProvider:

    def __init__(self):
        self.expenses_category_tree = CategoryTreeProvider().provide(TransactionTypeEnum.EXPENSES)

    @transaction.atomic
    def provide(self, bank_account):
        number_of_descendants = 0

        try:
            budget_tree = BudgetTree.objects.get(bank_account=bank_account)
        except ObjectDoesNotExist:
            budget_tree = BudgetTree(bank_account=bank_account)
            root = self.expenses_category_tree.root
            children = root.cached_children
            root_node = BudgetTreeNode(category=root, amount=-1)
            root_node.save()
            number_of_descendants += 1
            for child in children:
                number_of_descendants = self.handle_child(child, root_node, number_of_descendants)
            root_node.save()
            budget_tree.root = root_node
            budget_tree.save()

        return budget_tree

    def handle_child(self, category, parent, number_of_descendants):
        budget_tree_node = BudgetTreeNode(category=category, amount=0, parent=parent)
        budget_tree_node.save()
        number_of_descendants += 1
        for child in category.cached_children:
            number_of_descendants = self.handle_child(child, budget_tree_node, number_of_descendants)
        return number_of_descendants
