import unittest
from datetime import datetime
from pybackend.period import Month, Period, Grouping, Quarter


class TestPeriod(unittest.TestCase):

    def setUp(self):
        self.start_date = datetime(2023, 1, 1)
        self.end_date = datetime(2023, 1, 31)
        self.grouping = Grouping.MONTH
        self.period = Period(start=self.start_date, end=self.end_date, grouping=self.grouping)

    def test_init(self):
        self.assertEqual(self.period.start, datetime(2023, 1, 1, 0, 0))
        self.assertEqual(self.period.end, datetime(2023, 1, 31, 23, 59, 59, 999999))
        self.assertEqual(self.period.grouping, Grouping.MONTH)
        self.assertEqual(self.period.value, "01/2023")

    def test_to_json(self):
        json_str = self.period.to_json()
        expected_json = '{"start": "2023-01-01T00:00:00", "end": "2023-01-31T23:59:59.999999", "grouping": "month", "value": "01/2023"}'
        self.assertEqual(json_str, expected_json)

    def test_from_json(self):
        json_str = '{"start": "2023-01-01T00:00:00", "end": "2023-01-31T23:59:59.999999", "grouping": "month", "value": "01/2023"}'
        period_from_json = Period.from_json(json_str)
        self.assertEqual(period_from_json, self.period)

    def test_lt(self):
        other_period = Period(start=datetime(2023, 2, 1), end=datetime(2023, 2, 28), grouping=Grouping.MONTH)
        self.assertTrue(self.period < other_period)

    def test_eq(self):
        same_period = Period(start=self.start_date, end=self.end_date, grouping=self.grouping)
        self.assertTrue(self.period == same_period)

    def test_hash(self):
        period_hash = hash(self.period)
        expected_hash = hash((self.period.start, self.period.end, self.period.grouping, self.period.value))
        self.assertEqual(period_hash, expected_hash)


class TestQuarter(unittest.TestCase):

    def test_init(self):
        date = datetime(2023, 1, 15)
        quarter = Quarter.from_date(date)
        self.assertEqual(quarter.quarter_nr, 1)
        self.assertEqual(quarter.start, datetime(2023, 1, 1))
        self.assertEqual(quarter.end, datetime(2023, 3, 31, 23, 59, 59, 999999))

    def test_get_previous(self):
        date = datetime(2023, 4, 15)
        quarter = Quarter.from_date(date)
        previous_quarter = quarter.get_previous()
        self.assertEqual(previous_quarter.quarter_nr, 1)
        self.assertEqual(previous_quarter.start, datetime(2023, 1, 1))
        self.assertEqual(previous_quarter.end, datetime(2023, 3, 31, 23, 59, 59, 999999))

    def test_get_next(self):
        date = datetime(2023, 1, 15)
        quarter = Quarter.from_date(date)
        next_quarter = quarter.get_next()
        self.assertEqual(next_quarter.quarter_nr, 2)
        self.assertEqual(next_quarter.start, datetime(2023, 4, 1))
        self.assertEqual(next_quarter.end, datetime(2023, 6, 30, 23, 59, 59, 999999))


class TestMonth(unittest.TestCase):

    def test_init(self):
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        month = Month(start=start_date, end=end_date)
        self.assertEqual(month.start, datetime(2023, 1, 1, 0, 0))
        self.assertEqual(month.end, datetime(2023, 1, 31, 23, 59, 59, 999999))
        self.assertEqual(month.grouping, Grouping.MONTH)
        self.assertEqual(month.value, "01/2023")

    def test_next(self):
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        month = Month(start=start_date, end=end_date)
        next_month = month.next()
        self.assertEqual(next_month.start, datetime(2023, 2, 1, 0, 0))
        self.assertEqual(next_month.end, datetime(2023, 2, 28, 23, 59, 59, 999999))

    def test_previous(self):
        start_date = datetime(2023, 2, 1)
        end_date = datetime(2023, 2, 28)
        month = Month(start=start_date, end=end_date)
        previous_month = month.previous()
        self.assertEqual(previous_month.start, datetime(2023, 1, 1, 0, 0))
        self.assertEqual(previous_month.end, datetime(2023, 1, 31, 23, 59, 59, 999999))