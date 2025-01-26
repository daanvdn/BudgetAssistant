# src/main/python/budget-assistant-backend-django/pybackend/services/analysis_service.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from django_pandas.io import read_frame
from enumfields.drf import EnumField
from enumfields.fields import CharEnumField
from pandas.core.groupby import DataFrameGroupBy
from rest_framework import serializers
from rest_framework.serializers import Serializer

from pybackend.commons import RevenueExpensesQuery, TransactionPredicates, TransactionTypeEnum
from pybackend.models import BudgetTree, BudgetTreeNode, Category, Transaction
from pybackend.period import Period, PeriodSerializer
from pybackend.serializers import SimpleCategorySerializer
from pybackend.utils import ListMultiMap


@dataclass
class ExpensesAndRevenueForPeriod:
    period: Period
    revenue: float
    expenses: float
    balance: float


    def __eq__(self, other):
        return self.period == other.period and self.revenue == other.revenue and self.expenses == other.expenses and self.balance == other.balance

    def __hash__(self):
        return hash((self.period, self.revenue, self.expenses, self.balance))


class ExpensesAndRevenueForPeriodSerializer(Serializer):
    period = PeriodSerializer()
    revenue = serializers.FloatField()
    expenses = serializers.FloatField()
    balance = serializers.FloatField()

    def get_period(self, obj):
        return obj.period.value

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        period = PeriodSerializer().create(validated_data['period'])
        validated_data['period'] = period
        return validated_data

    def create(self, validated_data):
        return ExpensesAndRevenueForPeriod(**validated_data)


@dataclass
class PeriodAndAmount:
    period: Period
    amount: float
    is_anomaly: Optional[bool]= None


class PeriodAndAmountSerializer(Serializer):
    period = PeriodSerializer()
    amount = serializers.FloatField()
    is_anomaly = serializers.BooleanField(required=False, allow_null=True)

    def create(self, validated_data):
        period = PeriodSerializer().create(validated_data['period'])
        return PeriodAndAmount(period=period, amount=validated_data['amount'], is_anomaly=validated_data.get('is_anomaly'))





@dataclass
class CategoryAndAmount:
    category: Category
    amount: float
    is_revenue: bool



class CategoryAndAmountSerializer(Serializer):
    category = SimpleCategorySerializer()
    amount = serializers.FloatField()
    is_revenue = serializers.BooleanField()


    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        category = Category.objects.get(qualified_name=data['category']['qualified_name'])
        validated_data['category'] = category
        return validated_data

    def create(self, validated_data):
        return CategoryAndAmount(**validated_data)


@dataclass
class DistributionByCategoryForPeriodChartData:
    period: Period
    transaction_type: TransactionTypeEnum
    entries: List[CategoryAndAmount]



class DistributionByCategoryForPeriodChartDataSerializer(Serializer):
    period = PeriodSerializer(required=True)
    transaction_type = EnumField(TransactionTypeEnum)
    entries = CategoryAndAmountSerializer(many=True)

    class Meta:
        model = DistributionByCategoryForPeriodChartData
        fields = ['period', 'transaction_type', 'entries']

    def create(self, validated_data):
        entries_data = validated_data.pop('entries')
        period = PeriodSerializer().create(validated_data.pop('period'))
        entries = [CategoryAndAmountSerializer().create(entry) for entry in entries_data]
        return DistributionByCategoryForPeriodChartData(**validated_data, period=period, entries=entries)




@dataclass
class CategoryAndPeriodKey:
    category: Category
    period: Period

    def __eq__(self, __value):
        return self.category == __value.category and self.period == __value.period

    def __hash__(self):
        return hash((self.category, self.period))


@dataclass
class DistributionByCategoryForPeriodTableData:
    category: Category
    entries: List[PeriodAndAmount]
    is_revenue: bool



class DistributionByCategoryForPeriodTableDataSerializer(Serializer):
    category = SimpleCategorySerializer()
    entries = PeriodAndAmountSerializer(many=True)
    is_revenue = serializers.BooleanField()


    def create(self, validated_data):
        category = Category.objects.get(qualified_name=validated_data['category']['qualified_name'])
        entries = [PeriodAndAmountSerializer().create(entry) for entry in validated_data['entries']]
        return DistributionByCategoryForPeriodTableData(category=category, entries=entries, is_revenue=validated_data['is_revenue'])



@dataclass
class RevenueAndExpensesPerPeriodAndCategory:
    chart_data_revenue: List[DistributionByCategoryForPeriodChartData]
    chart_data_expenses: List[DistributionByCategoryForPeriodChartData]
    table_data_revenue: List[DistributionByCategoryForPeriodTableData]
    table_data_expenses: List[DistributionByCategoryForPeriodTableData]
    table_column_names_revenue: List[str]
    table_column_names_expenses: List[str]

    @staticmethod
    def empty_instance():
        return RevenueAndExpensesPerPeriodAndCategory(chart_data_revenue=[], chart_data_expenses=[],
                                                         table_data_expenses=[], table_data_revenue=[],
                                                         table_column_names_revenue=[], table_column_names_expenses=[])


class RevenueAndExpensesPerPeriodAndCategorySerializer(Serializer):
    chart_data_revenue =  serializers.ListField(child=DistributionByCategoryForPeriodChartDataSerializer())
    chart_data_expenses = serializers.ListField(child=DistributionByCategoryForPeriodChartDataSerializer())
    table_data_revenue = serializers.ListField(child=DistributionByCategoryForPeriodTableDataSerializer())
    table_data_expenses = serializers.ListField(child=DistributionByCategoryForPeriodTableDataSerializer())
    table_column_names_revenue = serializers.ListField(child=serializers.CharField())
    table_column_names_expenses = serializers.ListField(child=serializers.CharField())
    class Meta:
        model = RevenueAndExpensesPerPeriodAndCategory
        fields = [
            'chart_data_revenue',
            'chart_data_expenses',
            'table_data_revenue',
            'table_data_expenses',
            'table_column_names_revenue',
            'table_column_names_expenses'

        ]

    def create(self, validated_data):
        chart_data_revenue = [DistributionByCategoryForPeriodChartDataSerializer().create(item) for item in validated_data['chart_data_revenue']]
        chart_data_expenses = [DistributionByCategoryForPeriodChartDataSerializer().create(item) for item in validated_data['chart_data_expenses']]
        table_data_revenue = [DistributionByCategoryForPeriodTableDataSerializer().create(item) for item in validated_data['table_data_revenue']]
        table_data_expenses = [DistributionByCategoryForPeriodTableDataSerializer().create(item) for item in validated_data['table_data_expenses']]
        return RevenueAndExpensesPerPeriodAndCategory(chart_data_revenue=chart_data_revenue,
                                                      chart_data_expenses=chart_data_expenses,
                                                      table_data_revenue=table_data_revenue,
                                                      table_data_expenses=table_data_expenses,
                                                      table_column_names_revenue=validated_data['table_column_names_revenue'],
                                                      table_column_names_expenses=validated_data['table_column_names_expenses'])



@dataclass
class BudgetTrackerResultNode:
    children: List['BudgetTrackerResultNode'] = field(default_factory=list)
    category: Optional[Category] = None
    budget: Optional[int] = None
    amounts_for_period: Dict[str, float] = field(default_factory=dict)

    def __init__(self, category: Optional[Category] = None, budget: Optional[int] = None,
                 children: Optional[List['BudgetTrackerResultNode']] = None,
                 amounts_for_period: Optional[Dict[str, float]] = None):
        self.children = children if children else []
        self.category = category
        self.budget = budget
        if amounts_for_period:
            self.amounts_for_period = amounts_for_period

    def __eq__(self, other):
        return self.category == other.category and self.budget == other.budget and self.amounts_for_period == other.amounts_for_period and self.children == other.children

    def __hash__(self):
        return hash((self.category, self.budget, tuple(self.amounts_for_period.items()), tuple(self.children)))

    def add_amount_for_period(self, period: str, amount: float):
        self.amounts_for_period[period] = amount

    def add_child(self, child: 'BudgetTrackerResultNode'):
        self.children.append(child)



class BudgetTrackerResultNodeSerializer(Serializer):
    children = serializers.SerializerMethodField()
    category = serializers.SerializerMethodField()
    budget = serializers.IntegerField()
    amounts_for_period = serializers.DictField()

    def get_children(self, obj):
        # the needs to be a recursive method because every child can have children of its owwn
        return BudgetTrackerResultNodeSerializer(obj.children, many=True).data

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        qualified_name = data['category']
        category = Category.objects.get(qualified_name=qualified_name)
        validated_data['category'] = category
        children = data.get('children', [])
        # deserialize children recursively
        children_deserialized = [self.to_internal_value(child) for child in children]
        validated_data['children'] = children_deserialized
        return validated_data

    def get_category(self, obj):
        return obj.category.qualified_name

    def create(self, validated_data):
        children_data = validated_data.pop('children', [])
        node = BudgetTrackerResultNode(**validated_data)
        for child_data in children_data:
            child_node = self.create(child_data)
            node.add_child(child_node)
        return node



@dataclass
class BudgetTrackerResult:
    FIXED_COLS = ["category", "categoryId", "budget"]
    data: List[BudgetTrackerResultNode]
    columns: List[str]

    def __init__(self, data: List[BudgetTrackerResultNode], columns: List[str]):
        self.data = data
        self.columns = BudgetTrackerResult.FIXED_COLS.copy()
        # add all items from 'columns' that are not in FIXED_COLS
        self.columns.extend([x for x in columns if x not in BudgetTrackerResult.FIXED_COLS])
        # self.sanity_check() #fixme: reimplement if this method is still needed


    def sanity_check(self):
        if not self.columns:
            raise ValueError("Columns must be set")
        # recursively check all BudgetTrackerResultNode objects to determine if data always contains the same keys as columns and in the same order
        for node in self.data:
            if list(node.data.keys()) != self.columns:
                raise ValueError("Columns must match data keys")
            for child in node.children:
                if list(child.data.keys()) != self.columns:
                    raise ValueError("Columns must match data keys")


class BudgetTrackerResultSerializer(Serializer):
    data = serializers.SerializerMethodField()
    columns = serializers.ListField(child=serializers.CharField())

    def to_internal_value(self, data):
        internal = super().to_internal_value(data)
        internal['data'] = [BudgetTrackerResultNodeSerializer().to_internal_value(item) for item in data['data']]
        return internal
    def get_data(self, obj):
        return BudgetTrackerResultNodeSerializer(obj.data, many=True).data

    def create(self, validated_data):
        data = validated_data['data']
        data_deserialized = [BudgetTrackerResultNodeSerializer().create(item) for item in data]
        columns = validated_data['columns']
        return BudgetTrackerResult(data=data_deserialized, columns=columns)


class TransactionDistributionHandler:

    def __init__(self, revenue_expenses_query: RevenueExpensesQuery):
        self.revenue_expenses_query = revenue_expenses_query

    def _check_sign(self, float_value: float):
        if self.revenue_expenses_query.transaction_type == TransactionTypeEnum.REVENUE:
            assert float_value >= 0.0
        elif self.revenue_expenses_query.transaction_type == TransactionTypeEnum.EXPENSES:
            assert float_value < 0.0

    def get_expenses_and_revenue_per_period(self) -> List[ExpensesAndRevenueForPeriod]:

        def get_negative_and_positive_sums(transactions: List[Transaction]) -> Tuple[float, float]:
            negative_sum = 0.0
            positive_sum = 0.0

            for transaction in transactions:
                self._check_sign(transaction.amount)
                amount = transaction.amount
                if amount < 0:
                    negative_sum += amount
                else:
                    positive_sum += amount

            return negative_sum, positive_sum

        transactions = Transaction.objects.find_by_has_period_account_number_and_is_revenue(self.revenue_expenses_query)

        by_period = ListMultiMap[Period, Transaction]()

        for transaction in transactions:
            period = Period.from_transaction(transaction, self.revenue_expenses_query.grouping)
            by_period.put(period, transaction)

        distribution_by_transaction_type_for_period_list: List[ExpensesAndRevenueForPeriod] = []
        for period, transactions_for_period in by_period.items():
            negative_sum, positive_sum = get_negative_and_positive_sums(transactions_for_period)
            balance = positive_sum - abs(negative_sum)
            distribution_by_transaction_type_for_period_list.append(
                ExpensesAndRevenueForPeriod(period=period, revenue=positive_sum, expenses=negative_sum,
                                            balance=balance))

        # sort distribution_by_transaction_type_for_period_list by Period
        distribution_by_transaction_type_for_period_list.sort(key=lambda x: x.period.start)
        return distribution_by_transaction_type_for_period_list

    def get_expenses_and_revenue_per_period_pandas(self) -> List[ExpensesAndRevenueForPeriod]:
        transactions = Transaction.objects.find_by_has_period_account_number_and_is_revenue(self.revenue_expenses_query)

        def transaction_to_dict(t: Transaction):
            t_dict = t.__dict__
            t_dict['period'] = Period.from_transaction(t, self.revenue_expenses_query.grouping)
            return t_dict

        # Convert transactions to a DataFrame
        transactions_dicts = [transaction_to_dict(transaction) for transaction in transactions]
        df = pd.DataFrame(transactions_dicts)

        # Convert booking_date to datetime
        df['booking_date'] = pd.to_datetime(df['booking_date'])

        # Group by period and calculate sums
        grouped = df.groupby('period').agg(
            revenue=pd.NamedAgg(column='amount', aggfunc=lambda x: x[x >= 0].sum()),
            expenses=pd.NamedAgg(column='amount', aggfunc=lambda x: x[x < 0].sum())
        ).reset_index()

        # Calculate balance
        grouped['balance'] = grouped['revenue'] - grouped['expenses'].abs()

        # Convert to list of ExpensesAndRevenueForPeriod
        distribution_by_transaction_type_for_period_list = [
            ExpensesAndRevenueForPeriod(
                period=row['period'],
                revenue=row['revenue'],
                expenses=row['expenses'],
                balance=row['balance']
            )
            for _, row in grouped.iterrows()
        ]

        # Sort by period
        distribution_by_transaction_type_for_period_list.sort(key=lambda x: x.period.start)
        return distribution_by_transaction_type_for_period_list

    def get_expenses_and_revenue_per_period_and_category(self) -> RevenueAndExpensesPerPeriodAndCategory:
        transactions = Transaction.objects.find_by_has_period_account_number_and_is_revenue(self.revenue_expenses_query)

        def transaction_to_dict(t: Transaction):
            t_dict = t.__dict__
            t_dict['period'] = Period.from_transaction(t, self.revenue_expenses_query.grouping)
            if t.category.name in ("NO CATEGORY", "DUMMY CATEGORY"):
                t_dict['category'] = Category.no_category_object()
            else:
                t_dict['category'] = t.category
            t_dict['is_revenue'] = t.amount >= 0.0
            return t_dict

        # Convert transactions to a DataFrame
        transactions_dicts = [transaction_to_dict(transaction) for transaction in transactions]
        main_df = pd.DataFrame(transactions_dicts)
        # get all unique period in df and sort
        all_periods = main_df['period'].unique().tolist()
        all_periods = list(sorted(all_periods, key=lambda x: x.start))

        def process_df_for_transaction_type(a_df: pd.DataFrame, transaction_type: TransactionTypeEnum) -> Tuple[
            List[DistributionByCategoryForPeriodChartData], List[DistributionByCategoryForPeriodTableData], List[str]]:

            df = a_df[a_df['is_revenue'] == (transaction_type == TransactionTypeEnum.REVENUE)]
            # group revenue_df by period
            grouped_by_period = df.groupby('period')
            all_periods_for_transaction_type = list(sorted(grouped_by_period.groups.keys(), key=lambda x: x.start))


            # for every period in grouped create a DistributionByCategoryForPeriodChartData object.
            # The object contains the period, the transaction type, and a list of CategoryAndAmount objects
            distribution_by_category_for_period_chart_data_list: List[DistributionByCategoryForPeriodChartData] = []
            for period, group in grouped_by_period:
                if not isinstance(period, Period):
                    raise ValueError("Period must be a Period object")
                entries = []
                for category, category_group in group.groupby('category'):
                    if not isinstance(category, Category):
                        raise ValueError("Category must be a Category object")
                    entries.append(
                        CategoryAndAmount(category=category, amount=category_group['amount'].sum(),
                                          is_revenue=transaction_type == TransactionTypeEnum.REVENUE))
                distribution_by_category_for_period_chart_data_list.append(
                    DistributionByCategoryForPeriodChartData(period=period, transaction_type=transaction_type,
                                                             entries=entries))

            # sort distribution_by_category_for_period_chart_data_list by Period
            distribution_by_category_for_period_chart_data_list.sort(key=lambda x: x.period.start)


            # group df by category
            grouped_by_category: DataFrameGroupBy = df.groupby('category')
            # sort grouped by category qualified_name
            # get the categories from grouped_by_category and sort them by qualified_name
            categories = sorted(grouped_by_category.groups.keys(), key=lambda x: x.qualified_name)
            # for every category in grouped create a DistributionByCategoryForPeriodTableData object.
            # The object contains the category, a list of PeriodAndAmount objects, and a boolean is_revenue
            distribution_by_category_for_period_table_data_list: List[DistributionByCategoryForPeriodTableData] = []
            for category in categories:
                if not isinstance(category, Category):
                    raise ValueError("Category must be a Category object!")
                group = grouped_by_category.get_group(category)
                entries = []
                for period in all_periods_for_transaction_type:
                    amount = group[group['period'] == period]['amount'].sum()
                    entries.append(PeriodAndAmount(period=period, amount=float(amount), is_anomaly=None))
                if len(all_periods_for_transaction_type) != len(entries):
                    raise ValueError("Length of periods and entries must be equal!")
                distribution_by_category_for_period_table_data = DistributionByCategoryForPeriodTableData(
                    category=category, entries=entries, is_revenue=transaction_type == TransactionTypeEnum.REVENUE)
                distribution_by_category_for_period_table_data = self._mark_anomalies(
                    distribution_by_category_for_period_table_data)
                distribution_by_category_for_period_table_data_list.append(
                    distribution_by_category_for_period_table_data)

            table_column_names = ['category', 'category_id'] + [x.value for x in all_periods_for_transaction_type]

            return distribution_by_category_for_period_chart_data_list, distribution_by_category_for_period_table_data_list, table_column_names

        chart_revenue, table_revenue, revenue_table_columns = process_df_for_transaction_type(main_df,
                                                                                              TransactionTypeEnum.REVENUE)
        chart_expenses, table_expenses, expenses_table_columns = process_df_for_transaction_type(main_df,
                                                                                                 TransactionTypeEnum.EXPENSES)
        return RevenueAndExpensesPerPeriodAndCategory(chart_data_revenue=chart_revenue,
                                                      chart_data_expenses=chart_expenses,
                                                      table_data_revenue=table_revenue,
                                                      table_data_expenses=table_expenses,
                                                      table_column_names_revenue=revenue_table_columns,
                                                      table_column_names_expenses=expenses_table_columns)

    def _mark_anomalies(self, distribution_by_category_for_period_table_data: DistributionByCategoryForPeriodTableData):
        # for the category associated with the DistributionByCategoryForPeriodTableData object I want to know if the total amount that is associated with that category for a given period is anomalous or not.
        # I will use z scores with a threshold set to 2 to calculate if the amount is anomalous.

        amounts = [x.amount for x in distribution_by_category_for_period_table_data.entries]
        z_scores = (amounts - np.mean(amounts)) / np.std(amounts)
        distribution_by_category_for_period_table_data.entries = [
            PeriodAndAmount(period=x.period, amount=float(x.amount), is_anomaly=bool(abs(z_scores[i]) > 2)) for i, x in
            enumerate(distribution_by_category_for_period_table_data.entries)]

        return distribution_by_category_for_period_table_data


class BudgetTracker(TransactionDistributionHandler):
    def __init__(self, revenue_expenses_query: RevenueExpensesQuery, budget_tree: BudgetTree):
        super().__init__(revenue_expenses_query)
        self.budget_tree = budget_tree

    def get_budget_tracker_result(self) -> BudgetTrackerResult:
        revenue_and_expenses_per_period_and_category: RevenueAndExpensesPerPeriodAndCategory = super().get_expenses_and_revenue_per_period_and_category()
        expenses = revenue_and_expenses_per_period_and_category.table_data_expenses
        expenses_dict: Dict[Category, DistributionByCategoryForPeriodTableData] = {x.category: x for x in expenses}
        root = BudgetTrackerResultNode()
        children: List[BudgetTreeNode] = self.budget_tree.cached_children
        for child in children:
            self._handle_child(child, root, expenses_dict)
        return BudgetTrackerResult(data=root.children,
                                   columns=revenue_and_expenses_per_period_and_category.table_column_names_expenses)

    def _handle_child(self, budget_tree_node: BudgetTreeNode, parent: BudgetTrackerResultNode,
                      data_by_category: Dict[Category, DistributionByCategoryForPeriodTableData]):
        category = budget_tree_node.category
        if category in data_by_category:
            entries: List[PeriodAndAmount] = data_by_category[category].entries
            node = BudgetTrackerResultNode(category=category, budget=budget_tree_node.amount)
            for entry in entries:
                node.add_amount_for_period(entry.period.value, entry.amount)
            parent.add_child(node)
            children = budget_tree_node.cached_children
            for child in children:
                self._handle_child(child, node, data_by_category)

@dataclass
class Dataset:
    """Represents a dataset with a label and corresponding data."""
    label: str = field(metadata={"description": "The label for the dataset. This corresponds to Category.qualified_name"})
    data: List[float]
class DatasetSerializer(Serializer):
    label: str = serializers.CharField()
    data: List[float] = serializers.ListField(child=serializers.FloatField())

    def create(self, validated_data):
        return Dataset(**validated_data)

@dataclass
class CategoryDetailsForPeriodHandlerResult:
    labels: List[str]
    datasets: List[Dataset]

class CategoryDetailsForPeriodHandlerResultSerializer(Serializer):
    labels = serializers.ListField(child=serializers.CharField())
    datasets = DatasetSerializer(many=True)

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        dataset_serializer = DatasetSerializer(many=True, data=validated_data['datasets'])
        if not dataset_serializer.is_valid():
            raise serializers.ValidationError(dataset_serializer.errors)
        validated_data['datasets'] =  [Dataset(**item) for item in dataset_serializer.validated_data]
        return validated_data

    def create(self, validated_data):
        return CategoryDetailsForPeriodHandlerResult(**validated_data)


class CategoryDetailsForPeriodHandler:
    """fixme: add unittests"""

    def __init__(self, revenue_expenses_query: RevenueExpensesQuery, parent_category_qualified_name:str):
        self.revenue_expenses_query = revenue_expenses_query
        if parent_category_qualified_name:
            self.parent_category = Category.objects.get(qualified_name=parent_category_qualified_name)
            self.legal_category_ids = {self.parent_category.id}
            self.legal_category_ids.update(category.id for category in Category.objects._cache_descendants(self.parent_category))
            self.no_category = False
        else:
            self.no_category = True

    def get_category_details_for_period(self) -> CategoryDetailsForPeriodHandlerResult:

        if self.no_category:
            filter = TransactionPredicates.has_period_account_number_and_is_revenue_and_category_is_null(self.revenue_expenses_query)
        else:
            filter = TransactionPredicates.has_period_account_number_and_is_revenue_and_has_category(self.revenue_expenses_query, self.legal_category_ids)
        transactions = Transaction.objects.filter(filter)
        #create a pandas dataframe with all the transactions
        df:pd.DataFrame = read_frame(transactions)
        #add a column called 'period'. This column will contain the period for each transaction. A period can be create by calling the Period.from_transaction method
        df['period'] = df.apply(lambda row: Period.from_transaction(row, self.revenue_expenses_query.grouping), axis=1)
        #get all distinct periods
        periods = df['period'].unique()
        #sort the periods
        periods = list(sorted(periods))
        #group the df by category
        grouped_by_category = df.groupby('category')
        #loop over categories in grouped_by_category
        datasets = []
        parent_category_dataset = None
        for category, group in grouped_by_category:
            #create a list of datasets

            amounts_for_period = []
            #loop over periods
            for period in periods:
                #get all transaction of 'group' that are in the current period
                transactions_for_period = group[group['period'] == period]
                #get the sum of the amount for the group
                amount_for_period = transactions_for_period['amount'].sum()
                amounts_for_period.append(amount_for_period)

            #create a dataset object
            dataset = Dataset(label=category.qualified_name, data=amounts_for_period)
            if self.no_category or category.qualified_name == self.revenue_expenses_query.category.qualified_name:
                parent_category_dataset = dataset
            else:
                #add the dataset to the list of datasets
                datasets.append(dataset)
                #create a CategoryDetailsForPeriodHandlerResult object
            sorted_datasets = [parent_category_dataset]
            sorted_datasets.extend(sorted(datasets, key=lambda x: x.label))
            return CategoryDetailsForPeriodHandlerResult(labels=[x.value for x in periods], datasets=sorted_datasets)






        return CategoryDetailsForPeriodHandlerResult(labels=[], datasets=[])




