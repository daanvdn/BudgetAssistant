import datetime
import importlib.resources as pkg_resources
import io
from collections import namedtuple
from typing import Any, Callable, Dict, List, Tuple

import pandas as pd
from django.test import TestCase
from lxml import etree
from model_bakery import baker
from polyfactory.factories import DataclassFactory

from tests.utils import RevenueAndExpensesPerPeriodAndCategoryFactory, fake
from pybackend.analysis import BudgetTrackerResult, BudgetTrackerResultNode, BudgetTrackerResultNodeSerializer, \
    BudgetTrackerResultSerializer, CategoryAndAmount, CategoryAndAmountSerializer, \
    CategoryDetailsForPeriodHandlerResult, CategoryDetailsForPeriodHandlerResultSerializer, Dataset, DatasetSerializer, \
    DistributionByCategoryForPeriodChartData, DistributionByCategoryForPeriodChartDataSerializer, \
    DistributionByCategoryForPeriodTableData, ExpensesAndRevenueForPeriod, PeriodAndAmount, \
    RevenueAndExpensesPerPeriodAndCategory, RevenueAndExpensesPerPeriodAndCategorySerializer, \
    TransactionDistributionHandler
from pybackend.commons import RecurrenceType, RevenueExpensesQuery, TransactionTypeEnum
from pybackend.models import BankAccount, Category, Transaction
from pybackend.period import Grouping, Month, Period, Quarter, Year

Transactions = namedtuple('Transactions', ['account', 'start_date', 'end_date', 'df'])


class Resources:
    def __init__(self):
        dfs: Dict[str, Any] = self._load_blocks_from_xml()
        self.transactions = dfs['transactions']
        self.distributions_per_period: Dict[Grouping, List[ExpensesAndRevenueForPeriod]] = {}
        self.distributions_per_period[Grouping.MONTH] = self._init_months_distribution(dfs['month'])
        self.distributions_per_period[Grouping.QUARTER] = self._init_quarters_distribution(dfs['quarter'])
        self.distributions_per_period[Grouping.YEAR] = self._init_years_distribution(dfs['year'])
        self.distributions_per_period_and_category: Dict[Grouping, RevenueAndExpensesPerPeriodAndCategory] = {}
        self.distributions_per_period_and_category[Grouping.MONTH] = dfs['month_categories']
        self.distributions_per_period_and_category[Grouping.QUARTER] = dfs['quarter_categories']
        self.distributions_per_period_and_category[Grouping.YEAR] = dfs['year_categories']

    def _load_blocks_from_xml(self) -> Dict[str, pd.DataFrame]:

        blocks = {}

        with pkg_resources.open_text('pybackend.tests.resources',
                                     "test_get_expenses_and_revenue_per_period_pivot_tables.xml",
                                     encoding='utf-8') as file:
            # load the xml file
            tree = etree.parse(file)

            def get_csv_data_in_tag(tag_name: str) -> pd.DataFrame:
                text = tree.xpath(tag_name)[0].text.strip()
                # split lines platform independent
                lines = text.splitlines()
                # remove empty lines
                lines = [line.strip() for line in lines if line.strip()]
                return pd.read_csv(io.StringIO('\n'.join(lines)), delimiter=';', header=0)

            blocks['transactions'] = self._init_transactions(get_csv_data_in_tag('/root/transactions'))
            blocks['year'] = get_csv_data_in_tag('/root/year')
            blocks['month'] = get_csv_data_in_tag('/root/month')
            blocks['quarter'] = get_csv_data_in_tag('/root/quarter')

            def get_chart_and_table_for_category_distribution(
                    grouping: Grouping) -> RevenueAndExpensesPerPeriodAndCategory:

                def parse_period(period: str) -> Period:
                    if grouping == Grouping.MONTH:
                        month, year = period.split('_')
                        return Month.from_month_and_year(int(month), int(year))
                    elif grouping == Grouping.QUARTER:
                        quarter, year = period.split('_')
                        return Quarter.from_quarter_nr_and_year(int(quarter), int(year))
                    elif grouping == Grouping.YEAR:
                        return Year.from_year(int(period))
                    else:
                        raise ValueError(f'Invalid grouping: {grouping}')

                def get_category_from_db(category_name: str) -> Category:
                    # get category from db based on 'name' field
                    try:
                        return Category.objects.get(name=category_name)
                    except Exception as e:
                        raise ValueError(f"Category with name {category_name} not found in database") from e

                def handle_chart_data() -> Tuple[
                    List[DistributionByCategoryForPeriodChartData], List[DistributionByCategoryForPeriodChartData]]:
                    def parse_csv_data(text: str) -> pd.DataFrame:
                        lines = text.splitlines()
                        # remove empty lines
                        lines = [line.strip() for line in lines if line.strip()]
                        return pd.read_csv(io.StringIO('\n'.join(lines)), delimiter=';', header=0)

                    def sort_chart_data(data: List[DistributionByCategoryForPeriodChartData]) -> List[
                        DistributionByCategoryForPeriodChartData]:
                        return list(sorted(data, key=lambda x: x.period))

                    def _validate_df(a_df: pd.DataFrame, a_grouping: Grouping, is_expenses: bool):
                        type = 'expenses' if is_expenses else 'revenue'
                        if len(a_df.columns) != 2:
                            raise ValueError(
                                f"Expected 2 columns in the {type} dataframe for grouping {a_grouping.value.lower()}")
                        if not all(
                                a_df['category'].notnull() & a_df['category'].str.strip() & a_df['amount'].notnull()):
                            raise ValueError(
                                f"Expected non-empty values in {type} the dataframe for grouping {a_grouping.value.lower()}")

                    chart = tree.xpath(f'/root/{grouping.value.lower()}_categories/chart')[0]
                    # get entries
                    # use xpath to get all entry tags inside chart
                    chart_data_revenue = []
                    chart_data_expenses = []
                    entries = chart.xpath('entry')

                    for entry in entries:
                        period = parse_period(entry.xpath(f'{grouping.value.lower()}')[0].text.strip())
                        expenses_element = entry.xpath('expenses')
                        # check if there are any expenses
                        if expenses_element and len(expenses_element) > 0:
                            expenses: pd.DataFrame = parse_csv_data(expenses_element[0].text.strip())
                            # check that the dataframe has two columns, else fail
                            _validate_df(expenses, grouping, True)
                            expenses_distribution_by_category_for_period_chart_data = DistributionByCategoryForPeriodChartData(
                                period=period, transaction_type=TransactionTypeEnum.EXPENSES,
                                entries=[CategoryAndAmount(category=get_category_from_db(row['category']),
                                                           amount=row['amount'], is_revenue=False)
                                         for index, row in expenses.iterrows()])
                            chart_data_expenses.append(expenses_distribution_by_category_for_period_chart_data)

                        revenue_element = entry.xpath('revenue')
                        if revenue_element and len(revenue_element) > 0:
                            revenue: pd.DataFrame = parse_csv_data(revenue_element[0].text.strip())
                            _validate_df(revenue, grouping, False)
                            revenue_distribution_by_category_for_period_chart_data = DistributionByCategoryForPeriodChartData(
                                period=period, transaction_type=TransactionTypeEnum.REVENUE,
                                entries=[CategoryAndAmount(category=get_category_from_db(row['category']),
                                                           amount=row['amount'], is_revenue=True)
                                         for index, row in revenue.iterrows()])
                            chart_data_revenue.append(revenue_distribution_by_category_for_period_chart_data)

                    return sort_chart_data(chart_data_revenue), sort_chart_data(chart_data_expenses)

                def handle_table_data() -> Tuple[
                    List[DistributionByCategoryForPeriodTableData], List[DistributionByCategoryForPeriodTableData]]:
                    def parse_csv_data(text: str) -> pd.DataFrame:
                        lines = text.splitlines()
                        # remove empty lines
                        lines = [line.strip() for line in lines if line.strip()]
                        return pd.read_csv(io.StringIO('\n'.join(lines)), delimiter=';', header=None)

                    def process_transaction_type(is_revenue: bool) -> List[DistributionByCategoryForPeriodTableData]:
                        table = tree.xpath(f'/root/{grouping.value.lower()}_categories/table')[0]
                        node_name = 'revenue' if is_revenue else 'expenses'
                        csv_string = table.xpath(node_name)[0].text.strip()
                        df = parse_csv_data(csv_string)
                        # get the first row of the df
                        first_row = df.iloc[0]
                        periods = []
                        for i in range(1, len(first_row)):
                            period = parse_period(first_row[i])
                            periods.append(period)

                        result = []
                        for index, row in df.iterrows():
                            if index == 0:
                                continue
                            category = get_category_from_db(row[0])
                            entries = []
                            for i in range(1, len(row)):
                                period = periods[i - 1]
                                amount = float(row[i])
                                entries.append(PeriodAndAmount(period=period, amount=float(amount), is_anomaly=None))

                            # sort entries by period
                            entries = list(sorted(entries, key=lambda x: x.period))
                            result.append(DistributionByCategoryForPeriodTableData(category=category, entries=entries,
                                                                                   is_revenue=is_revenue))
                        return result

                    return process_transaction_type(True), process_transaction_type(False)

                revenue_chart, expenses_chart = handle_chart_data()
                revenue_table, expenses_table = handle_table_data()

                def get_columns(data: List[DistributionByCategoryForPeriodChartData]) -> List[str]:
                    periods = [data.period for data in data]
                    periods = sorted(periods)
                    periods = [period.value for period in periods]
                    return ['category', 'category_id'] + periods

                revenue_cols = get_columns(revenue_chart)
                expenses_cols = get_columns(expenses_chart)
                return RevenueAndExpensesPerPeriodAndCategory(chart_data_revenue=revenue_chart,
                                                              chart_data_expenses=expenses_chart,
                                                              table_data_revenue=revenue_table,
                                                              table_data_expenses=expenses_table,
                                                              table_column_names_revenue=revenue_cols,
                                                              table_column_names_expenses=expenses_cols)

            blocks['year_categories'] = get_chart_and_table_for_category_distribution(Grouping.YEAR)
            blocks['month_categories'] = get_chart_and_table_for_category_distribution(Grouping.MONTH)
            blocks['quarter_categories'] = get_chart_and_table_for_category_distribution(Grouping.QUARTER)

        return blocks

    def _init_transactions(self, df: pd.DataFrame) -> 'Transactions':
        account = baker.make(BankAccount, account_number="123456")

        # parse the string in the 'date' column as a datetime object. The format is DD/MM/YYYY
        df['date'] = pd.to_datetime(df['date'], format='%d/%m/%Y')
        category_dict = {}
        # loop over the rows and create a transaction for each row use baker.make. store the trasnaction in the dataframe
        for index, row in df.iterrows():
            category = row['category']
            type = 'EXPENSES' if category.split('_')[1].lower() == "expenses" else "REVENUE"
            if category not in category_dict:
                category_dict[category] = baker.make(Category, name=category, type=type, qualified_name=category)
            category = category_dict[category]

            transaction = baker.make(Transaction, amount=row['amount'],
                                     category=category,
                                     bank_account=account,
                                     booking_date=row['date'])
            df.at[index, 'transaction'] = transaction
        # get earliest and latest date from the dataframe
        start_date = df['date'].min()
        end_date = df['date'].max()
        return Transactions(account=account, start_date=start_date,
                            end_date=end_date, df=df)

    def _init_months_distribution(self, df: pd.DataFrame) -> List[ExpensesAndRevenueForPeriod]:
        expected: List[ExpensesAndRevenueForPeriod] = []
        # loop over the rows in the df
        for index, row in df.iterrows():
            month = row['month']
            month_nr = month.split('_')[0]
            year = month.split('_')[1]
            expected.append(
                ExpensesAndRevenueForPeriod(period=Month.from_month_and_year(int(month_nr), int(year)),
                                            revenue=int(row['revenue']),
                                            expenses=int(row['expenses']),
                                            balance=(row['balance'])))

        return expected

    def _init_quarters_distribution(self, df: pd.DataFrame) -> List[ExpensesAndRevenueForPeriod]:
        expected: List[ExpensesAndRevenueForPeriod] = []
        # loop over the rows in the df
        for index, row in df.iterrows():
            quarter = row['quarter']
            quarter_nr = quarter.split('_')[0]
            year = quarter.split('_')[1]
            quarter = Quarter.from_quarter_nr_and_year(int(quarter_nr), int(year))
            expected.append(ExpensesAndRevenueForPeriod(period=quarter, revenue=int(row['revenue']),
                                                        expenses=int(row['expenses']),
                                                        balance=(row['balance'])))
        return expected

    def _init_years_distribution(self, df: pd.DataFrame) -> List[ExpensesAndRevenueForPeriod]:
        expected: List[ExpensesAndRevenueForPeriod] = []
        # loop over the rows in the df
        for index, row in df.iterrows():
            year = row['year']

            expected.append(
                ExpensesAndRevenueForPeriod(period=Year.from_year(int(year)), revenue=int(row['revenue']),
                                            expenses=int(row['expenses']),
                                            balance=(row['balance'])))
        return expected


class TransactionDistributionHandlerTests(TestCase):

    def setUp(self):
        # self.maxDiff = None
        pass

    def test_get_expenses_and_revenue_per_period_year(self):
        fn = lambda x: TransactionDistributionHandler(x).get_expenses_and_revenue_per_period()
        self._do_test_get_expenses_and_revenue_per_period(Grouping.YEAR, fn)

    def test_get_expenses_and_revenue_per_period_year_pandas(self):
        fn = lambda x: TransactionDistributionHandler(x).get_expenses_and_revenue_per_period_pandas()
        self._do_test_get_expenses_and_revenue_per_period(Grouping.YEAR, fn)

    def test_get_expenses_and_revenue_per_period_quarter(self):

        fn = lambda x: TransactionDistributionHandler(x).get_expenses_and_revenue_per_period()
        self._do_test_get_expenses_and_revenue_per_period(Grouping.QUARTER, fn)

    def test_get_expenses_and_revenue_per_period_quarter_pandas(self):

        fn = lambda x: TransactionDistributionHandler(x).get_expenses_and_revenue_per_period_pandas()
        self._do_test_get_expenses_and_revenue_per_period(Grouping.QUARTER, fn)

    def test_get_expenses_and_revenue_per_period_month(self):
        fn = lambda x: TransactionDistributionHandler(x).get_expenses_and_revenue_per_period()
        self._do_test_get_expenses_and_revenue_per_period(Grouping.MONTH, fn)

    def test_get_expenses_and_revenue_per_period_month_pandas(self):
        fn = lambda x: TransactionDistributionHandler(x).get_expenses_and_revenue_per_period_pandas()
        self._do_test_get_expenses_and_revenue_per_period(Grouping.MONTH, fn)

    def _do_test_get_expenses_and_revenue_per_period(self, grouping: Grouping, get_expenses_and_revenue_per_period_fn):
        resources = Resources()
        start_date = resources.transactions.start_date
        end_date = resources.transactions.end_date
        account_number = resources.transactions.account.account_number
        query = RevenueExpensesQuery(
            account_number=account_number, transaction_type=TransactionTypeEnum.BOTH, start=start_date,
            end=end_date, grouping=grouping, revenue_recurrence=RecurrenceType.BOTH,
            expenses_recurrence=RecurrenceType.BOTH
        )

        actual: List[ExpensesAndRevenueForPeriod] = get_expenses_and_revenue_per_period_fn(query)
        # (
        # handler.get_expenses_and_revenue_per_period())
        expected = resources.distributions_per_period[grouping]
        self.assertEqual(len(actual), len(expected))
        actual = sorted(actual, key=lambda x: x.period)
        expected = sorted(expected, key=lambda x: x.period)
        self.assertListEqual(actual, expected)

    def test_get_expenses_and_revenue_per_period_no_transactions(self):
        account = baker.make(BankAccount, account_number="123456")
        query = RevenueExpensesQuery(
            account_number="123456", transaction_type=TransactionTypeEnum.BOTH, start=datetime.datetime(2023, 1, 1),
            end=datetime.datetime(2023, 12, 31), grouping=Grouping.MONTH, revenue_recurrence=RecurrenceType.BOTH,
            expenses_recurrence=RecurrenceType.BOTH
        )
        handler = TransactionDistributionHandler(query)
        result = handler.get_expenses_and_revenue_per_period()
        self.assertEqual(len(result), 0)

    def test_get_expenses_and_revenue_per_period_and_category_year(self):
        self._do_test_get_expenses_and_revenue_per_period_and_category(Grouping.YEAR)

    def test_get_expenses_and_revenue_per_period_and_category_month(self):
        self._do_test_get_expenses_and_revenue_per_period_and_category(Grouping.MONTH)

    def test_get_expenses_and_revenue_per_period_and_category_quarter(self):
        self._do_test_get_expenses_and_revenue_per_period_and_category(Grouping.QUARTER)

    def _do_test_get_expenses_and_revenue_per_period_and_category(self, grouping: Grouping):

        resources = Resources()
        start_date = resources.transactions.start_date
        end_date = resources.transactions.end_date
        account_number = resources.transactions.account.account_number
        query = RevenueExpensesQuery(
            account_number=account_number, transaction_type=TransactionTypeEnum.BOTH, start=start_date,
            end=end_date, grouping=grouping, revenue_recurrence=RecurrenceType.BOTH,
            expenses_recurrence=RecurrenceType.BOTH
        )
        expected = resources.distributions_per_period_and_category[grouping]
        handler = TransactionDistributionHandler(query)
        actual: RevenueAndExpensesPerPeriodAndCategory = handler.get_expenses_and_revenue_per_period_and_category()
        expected_chart_data_expenses = expected.chart_data_expenses
        actual_chart_data_expenses = actual.chart_data_expenses
        self.assertIsNotNone(actual_chart_data_expenses)
        self.assertIsNotNone(expected_chart_data_expenses)

        def compare_lists_chart_data(actual: List[DistributionByCategoryForPeriodChartData],
                                     expected: List[DistributionByCategoryForPeriodChartData]):
            self.assertListEqual(actual, expected)

            self.assertEqual(len(actual), len(expected))
            for i in range(len(actual)):
                self.assertEqual(actual[i].period, expected[i].period)
                self.assertEqual(actual[i].transaction_type, expected[i].transaction_type)
                self.assertEqual(len(actual[i].entries), len(expected[i].entries))
                for j in range(len(actual[i].entries)):
                    self.assertEqual(actual[i].entries[j].category, expected[i].entries[j].category)
                    self.assertEqual(actual[i].entries[j].amount, expected[i].entries[j].amount)
                    self.assertEqual(actual[i].entries[j].is_revenue, expected[i].entries[j].is_revenue)

        compare_lists_chart_data(actual_chart_data_expenses, expected_chart_data_expenses)

        expected_chart_data_revenue = expected.chart_data_revenue
        actual_chart_data_revenue = actual.chart_data_revenue
        self.assertIsNotNone(actual_chart_data_revenue)
        self.assertIsNotNone(expected_chart_data_revenue)
        compare_lists_chart_data(actual_chart_data_revenue, expected_chart_data_revenue)

        expected_table_data_revenue = expected.table_data_revenue
        actual_table_data_revenue = actual.table_data_revenue

        def compare_lists_table_data(actual: List[DistributionByCategoryForPeriodTableData],
                                     expected: List[DistributionByCategoryForPeriodTableData]):
            self.assertEqual(len(actual), len(expected))
            for i in range(len(actual)):
                self.assertEqual(actual[i].category, expected[i].category)
                self.assertEqual(actual[i].is_revenue, expected[i].is_revenue)
                self.assertEqual(len(actual[i].entries), len(expected[i].entries))
                for j in range(len(actual[i].entries)):
                    self.assertEqual(actual[i].entries[j].period, expected[i].entries[j].period)
                    self.assertEqual(actual[i].entries[j].amount, expected[i].entries[j].amount)
                    self.assertIsInstance(actual[i].entries[j].is_anomaly, bool)

        self.assertIsNotNone(actual_table_data_revenue)
        self.assertIsNotNone(expected_table_data_revenue)
        compare_lists_table_data(actual_table_data_revenue, expected_table_data_revenue)
        actual_table_data_expenses = actual.table_data_expenses
        expected_table_data_expenses = expected.table_data_expenses
        self.assertIsNotNone(actual_table_data_expenses)
        self.assertIsNotNone(expected_table_data_expenses)

        compare_lists_table_data(actual_table_data_expenses, expected_table_data_expenses)


class BudgetTrackerTests(TestCase):
    pass


class TestCategoryAndAmountSerializer(TestCase):

    def test_serialize_deserialize(self):
        category = baker.make(Category, name="a", qualified_name="a")
        category_and_amount = CategoryAndAmount(category=category, amount=100, is_revenue=True)
        serialized = CategoryAndAmountSerializer(category_and_amount).data
        serializer = CategoryAndAmountSerializer(data=serialized)
        if serializer.is_valid(raise_exception=True):
            deserialized = serializer.create(serializer.validated_data)
            self.assertEqual(category_and_amount, deserialized)


class BudgetTrackerResultNodeFactory(DataclassFactory[BudgetTrackerResultNode]):
    __allow_none_optionals__ = False
    ...
    MAX_DEPTH = 3
    CURRENT_DEPTH = 0
    SEEN_NAMES = set()

    @classmethod
    def category(cls):

        name = fake.word()
        while name in cls.SEEN_NAMES:
            name = fake.word()
        cls.SEEN_NAMES.add(name)
        return baker.make(Category, name=name, qualified_name=name)

    @classmethod
    def children(cls):
        if cls.CURRENT_DEPTH <= cls.MAX_DEPTH:
            cls.CURRENT_DEPTH += 1
            return BudgetTrackerResultNodeFactory.batch(2)


class TestBudgetTrackerResultNodeSerializer(TestCase):
    def test(self):
        node = BudgetTrackerResultNodeFactory.build()
        serialized = BudgetTrackerResultNodeSerializer(node).data
        serializer = BudgetTrackerResultNodeSerializer(data=serialized)
        if serializer.is_valid(raise_exception=True):
            deserialized = serializer.create(serializer.validated_data)
            self.assertEqual(node, deserialized)


class BudgetTrackerResultFactory(DataclassFactory[BudgetTrackerResult]):
    __allow_none_optionals__ = False

    @classmethod
    def data(cls):
        return [item for item in BudgetTrackerResultNodeFactory.build().children]


class TestBudgetTrackerResultSerializer(TestCase):

    def test(self):
        budget_tracker_result = BudgetTrackerResultFactory.build()
        serialized = BudgetTrackerResultSerializer(budget_tracker_result).data
        serializer = BudgetTrackerResultSerializer(data=serialized)
        if serializer.is_valid(raise_exception=True):
            deserialized = serializer.create(serializer.validated_data)
            self.assertEqual(budget_tracker_result, deserialized)


class DatasetFactory(DataclassFactory[Dataset]):
    ...


class TestDatasetSerializer(TestCase):
    def test(self):
        dataset = DatasetFactory.build()
        serialized = DatasetSerializer(dataset).data
        serializer = DatasetSerializer(data=serialized)
        if serializer.is_valid(raise_exception=True):
            deserialized = serializer.create(serializer.validated_data)
            self.assertEqual(dataset, deserialized)


class CategoryDetailsForPeriodHandlerResultFactory(DataclassFactory[CategoryDetailsForPeriodHandlerResult]):
    ...


class TestCategoryDetailsForPeriodHandlerResultSerializer(TestCase):
    def test(self):
        category_details_for_period_handler_result = CategoryDetailsForPeriodHandlerResultFactory.build()
        serialized = CategoryDetailsForPeriodHandlerResultSerializer(category_details_for_period_handler_result).data
        serializer = CategoryDetailsForPeriodHandlerResultSerializer(data=serialized)
        if serializer.is_valid(raise_exception=True):
            deserialized = serializer.create(serializer.validated_data)
            self.assertEquals(category_details_for_period_handler_result, deserialized)


class DistributionByCategoryForPeriodChartDataFactory(DataclassFactory[DistributionByCategoryForPeriodChartData]):
    __allow_none_optionals__ = False
    ...

    @classmethod
    def get_provider_map(cls) -> dict[Any, Callable[[], Any]]:
        providers_map = super().get_provider_map()

        def period():
            start = datetime.datetime(2020, 1, 1)
            end = datetime.datetime(2020, 1, 31)
            return Month(start, end)

        return {
            Period: lambda: period(),
            Category: lambda: baker.make(Category),
            **providers_map,
        }


class TestDistributionByCategoryForPeriodChartDataSerializer(TestCase):
    def test(self):
        dto = DistributionByCategoryForPeriodChartDataFactory.build()
        serialized = DistributionByCategoryForPeriodChartDataSerializer(dto).data
        serializer = DistributionByCategoryForPeriodChartDataSerializer(data=serialized)
        if serializer.is_valid(raise_exception=True):
            deserialized = serializer.create(serializer.validated_data)
            self.assertEqual(dto, deserialized)


class TestRevenueAndExpensesPerPeriodAndCategorySerializer(TestCase):
    def test(self):
        revenue_and_expenses_per_period_and_category = RevenueAndExpensesPerPeriodAndCategoryFactory.build()
        serialized = RevenueAndExpensesPerPeriodAndCategorySerializer(revenue_and_expenses_per_period_and_category).data
        serializer = RevenueAndExpensesPerPeriodAndCategorySerializer(data=serialized)
        if serializer.is_valid(raise_exception=True):
            deserialized = serializer.create(serializer.validated_data)
            self.assertEqual(revenue_and_expenses_per_period_and_category, deserialized)
