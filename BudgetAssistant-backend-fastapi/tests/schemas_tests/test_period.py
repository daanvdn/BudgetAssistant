"""Tests for Period schema classes."""

from datetime import date, datetime

import pytest

from schemas.common import Grouping
from schemas.period import (
    Month,
    Period,
    PeriodFromTransactionFactory,
    PeriodSchema,
    PeriodValueFormatter,
    Quarter,
    Year,
)


class TestPeriod:
    """Tests for the Period class."""

    def setup_method(self) -> None:
        """Set up test fixtures."""
        self.start_date = datetime(2023, 1, 1)
        self.end_date = datetime(2023, 1, 31)
        self.grouping = Grouping.MONTH
        self.period = Period(
            start=self.start_date, end=self.end_date, grouping=self.grouping
        )

    def test_init(self) -> None:
        """Test Period initialization."""
        assert self.period.start == datetime(2023, 1, 1, 0, 0)
        assert self.period.end == datetime(2023, 1, 31, 23, 59, 59, 999999)
        assert self.period.grouping == Grouping.MONTH
        assert self.period.value == "01/2023"

    def test_to_json(self) -> None:
        """Test Period JSON serialization."""
        json_str = self.period.to_json()
        expected_json = '{"start": "2023-01-01T00:00:00", "end": "2023-01-31T23:59:59.999999", "grouping": "MONTH", "value": "01/2023"}'
        assert json_str == expected_json

    def test_from_json(self) -> None:
        """Test Period JSON deserialization."""
        json_str = '{"start": "2023-01-01T00:00:00", "end": "2023-01-31T23:59:59.999999", "grouping": "MONTH", "value": "01/2023"}'
        period_from_json = Period.from_json(json_str)
        assert period_from_json == self.period

    def test_lt(self) -> None:
        """Test Period less than comparison."""
        other_period = Period(
            start=datetime(2023, 2, 1),
            end=datetime(2023, 2, 28),
            grouping=Grouping.MONTH,
        )
        assert self.period < other_period

    def test_gt(self) -> None:
        """Test Period greater than comparison."""
        other_period = Period(
            start=datetime(2022, 12, 1),
            end=datetime(2022, 12, 31),
            grouping=Grouping.MONTH,
        )
        assert self.period > other_period

    def test_eq(self) -> None:
        """Test Period equality comparison."""
        same_period = Period(
            start=self.start_date, end=self.end_date, grouping=self.grouping
        )
        assert self.period == same_period

    def test_hash(self) -> None:
        """Test Period hash."""
        period_hash = hash(self.period)
        expected_hash = hash(
            (
                self.period.start,
                self.period.end,
                self.period.grouping,
                self.period.value,
            )
        )
        assert period_hash == expected_hash

    def test_str(self) -> None:
        """Test Period string representation."""
        assert str(self.period) == "01/2023"

    def test_repr(self) -> None:
        """Test Period repr."""
        assert repr(self.period) == "01/2023"


class TestQuarter:
    """Tests for the Quarter class."""

    def test_init(self) -> None:
        """Test Quarter initialization from date."""
        date = datetime(2023, 1, 15)
        quarter = Quarter.from_date(date)
        assert quarter.quarter_nr == 1
        assert quarter.start == datetime(2023, 1, 1)
        assert quarter.end == datetime(2023, 3, 31, 23, 59, 59, 999999)

    def test_q2_from_date(self) -> None:
        """Test Quarter Q2 from date."""
        date = datetime(2023, 5, 15)
        quarter = Quarter.from_date(date)
        assert quarter.quarter_nr == 2
        assert quarter.start == datetime(2023, 4, 1)
        assert quarter.end == datetime(2023, 6, 30, 23, 59, 59, 999999)

    def test_q3_from_date(self) -> None:
        """Test Quarter Q3 from date."""
        date = datetime(2023, 8, 15)
        quarter = Quarter.from_date(date)
        assert quarter.quarter_nr == 3
        assert quarter.start == datetime(2023, 7, 1)
        assert quarter.end == datetime(2023, 9, 30, 23, 59, 59, 999999)

    def test_q4_from_date(self) -> None:
        """Test Quarter Q4 from date."""
        date = datetime(2023, 11, 15)
        quarter = Quarter.from_date(date)
        assert quarter.quarter_nr == 4
        assert quarter.start == datetime(2023, 10, 1)
        assert quarter.end == datetime(2023, 12, 31, 23, 59, 59, 999999)

    def test_get_previous(self) -> None:
        """Test get_previous returns the previous quarter."""
        date = datetime(2023, 4, 15)
        quarter = Quarter.from_date(date)
        previous_quarter = quarter.get_previous()
        assert previous_quarter.quarter_nr == 1
        assert previous_quarter.start == datetime(2023, 1, 1)
        assert previous_quarter.end == datetime(2023, 3, 31, 23, 59, 59, 999999)

    def test_get_previous_wrap_around(self) -> None:
        """Test get_previous wraps around to previous year's Q4."""
        date = datetime(2023, 2, 15)
        quarter = Quarter.from_date(date)
        previous_quarter = quarter.get_previous()
        assert previous_quarter.quarter_nr == 4
        assert previous_quarter.start == datetime(2022, 10, 1)
        assert previous_quarter.end == datetime(2022, 12, 31, 23, 59, 59, 999999)

    def test_get_next(self) -> None:
        """Test get_next returns the next quarter."""
        date = datetime(2023, 1, 15)
        quarter = Quarter.from_date(date)
        next_quarter = quarter.get_next()
        assert next_quarter.quarter_nr == 2
        assert next_quarter.start == datetime(2023, 4, 1)
        assert next_quarter.end == datetime(2023, 6, 30, 23, 59, 59, 999999)

    def test_get_next_wrap_around(self) -> None:
        """Test get_next wraps around to next year's Q1."""
        date = datetime(2023, 11, 15)
        quarter = Quarter.from_date(date)
        next_quarter = quarter.get_next()
        assert next_quarter.quarter_nr == 1
        assert next_quarter.start == datetime(2024, 1, 1)
        assert next_quarter.end == datetime(2024, 3, 31, 23, 59, 59, 999999)

    def test_from_quarter_nr_and_year(self) -> None:
        """Test creating a Quarter from quarter number and year."""
        quarter = Quarter.from_quarter_nr_and_year(3, 2023)
        assert quarter.quarter_nr == 3
        assert quarter.start == datetime(2023, 7, 1)
        assert quarter.end == datetime(2023, 9, 30, 23, 59, 59, 999999)


class TestMonth:
    """Tests for the Month class."""

    def test_init(self) -> None:
        """Test Month initialization."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        month = Month(start=start_date, end=end_date)
        assert month.start == datetime(2023, 1, 1, 0, 0)
        assert month.end == datetime(2023, 1, 31, 23, 59, 59, 999999)
        assert month.grouping == Grouping.MONTH
        assert month.value == "01/2023"

    def test_next(self) -> None:
        """Test getting the next month."""
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2023, 1, 31)
        month = Month(start=start_date, end=end_date)
        next_month = month.next()
        assert next_month.start == datetime(2023, 2, 1, 0, 0)
        assert next_month.end == datetime(2023, 2, 28, 23, 59, 59, 999999)

    def test_next_year_wrap(self) -> None:
        """Test next month wraps to next year."""
        month = Month.from_month_and_year(12, 2023)
        next_month = month.next()
        assert next_month.start == datetime(2024, 1, 1, 0, 0)
        assert next_month.end == datetime(2024, 1, 31, 23, 59, 59, 999999)

    def test_previous(self) -> None:
        """Test getting the previous month."""
        start_date = datetime(2023, 2, 1)
        end_date = datetime(2023, 2, 28)
        month = Month(start=start_date, end=end_date)
        previous_month = month.previous()
        assert previous_month.start == datetime(2023, 1, 1, 0, 0)
        assert previous_month.end == datetime(2023, 1, 31, 23, 59, 59, 999999)

    def test_previous_year_wrap(self) -> None:
        """Test previous month wraps to previous year."""
        month = Month.from_month_and_year(1, 2023)
        previous_month = month.previous()
        assert previous_month.start == datetime(2022, 12, 1, 0, 0)
        assert previous_month.end == datetime(2022, 12, 31, 23, 59, 59, 999999)

    def test_from_month_and_year(self) -> None:
        """Test creating a Month from month and year numbers."""
        month = Month.from_month_and_year(6, 2023)
        assert month.start == datetime(2023, 6, 1, 0, 0)
        assert month.end == datetime(2023, 6, 30, 23, 59, 59, 999999)
        assert month.value == "06/2023"

    def test_from_month_and_year_leap_year(self) -> None:
        """Test Month for February in a leap year."""
        month = Month.from_month_and_year(2, 2024)
        assert month.start == datetime(2024, 2, 1, 0, 0)
        assert month.end == datetime(2024, 2, 29, 23, 59, 59, 999999)


class TestYear:
    """Tests for the Year class."""

    def test_init(self) -> None:
        """Test Year initialization."""
        year = Year.from_year(2023)
        assert year.start == datetime(2023, 1, 1, 0, 0)
        assert year.end == datetime(2023, 12, 31, 23, 59, 59, 999999)
        assert year.grouping == Grouping.YEAR
        assert year.value == "2023 - 2023"

    def test_next(self) -> None:
        """Test getting the next year."""
        year = Year.from_year(2023)
        next_year = year.next()
        assert next_year.start == datetime(2024, 1, 1, 0, 0)
        assert next_year.end == datetime(2024, 12, 31, 23, 59, 59, 999999)

    def test_previous(self) -> None:
        """Test getting the previous year."""
        year = Year.from_year(2023)
        previous_year = year.previous()
        assert previous_year.start == datetime(2022, 1, 1, 0, 0)
        assert previous_year.end == datetime(2022, 12, 31, 23, 59, 59, 999999)


class TestPeriodValueFormatter:
    """Tests for the PeriodValueFormatter class."""

    def test_month_format(self) -> None:
        """Test month formatting."""
        formatter = PeriodValueFormatter()
        result = formatter.run(
            datetime(2023, 3, 15), datetime(2023, 3, 31), Grouping.MONTH
        )
        assert result == "03/2023"

    def test_quarter_format(self) -> None:
        """Test quarter formatting."""
        formatter = PeriodValueFormatter()
        result = formatter.run(
            datetime(2023, 1, 1), datetime(2023, 3, 31), Grouping.QUARTER
        )
        assert result == "01/2023 - 03/2023"

    def test_year_format(self) -> None:
        """Test year formatting."""
        formatter = PeriodValueFormatter()
        result = formatter.run(
            datetime(2023, 1, 1), datetime(2023, 12, 31), Grouping.YEAR
        )
        assert result == "2023 - 2023"

    def test_invalid_grouping(self) -> None:
        """Test invalid grouping raises error."""
        formatter = PeriodValueFormatter()
        # The Grouping enum has DAY and WEEK but formatter doesn't support them
        with pytest.raises(ValueError, match="Unexpected value for grouping"):
            formatter.run(datetime(2023, 1, 1), datetime(2023, 1, 7), Grouping.DAY)


class TestPeriodFromTransactionFactory:
    """Tests for the PeriodFromTransactionFactory class."""

    class MockTransaction:
        """Mock transaction for testing."""

        def __init__(self, booking_date: date) -> None:
            self.booking_date = booking_date

    def test_create_month_period(self) -> None:
        """Test creating a Month period from a transaction."""
        transaction = self.MockTransaction(date(2023, 6, 15))
        factory = PeriodFromTransactionFactory(transaction, Grouping.MONTH)
        period = factory.create()
        assert isinstance(period, Month)
        assert period.start == datetime(2023, 6, 1, 0, 0)
        assert period.end == datetime(2023, 6, 30, 23, 59, 59, 999999)

    def test_create_quarter_period(self) -> None:
        """Test creating a Quarter period from a transaction."""
        transaction = self.MockTransaction(date(2023, 5, 15))
        factory = PeriodFromTransactionFactory(transaction, Grouping.QUARTER)
        period = factory.create()
        assert isinstance(period, Quarter)
        assert period.quarter_nr == 2
        assert period.start == datetime(2023, 4, 1, 0, 0)
        assert period.end == datetime(2023, 6, 30, 23, 59, 59, 999999)

    def test_create_year_period(self) -> None:
        """Test creating a Year period from a transaction."""
        transaction = self.MockTransaction(date(2023, 6, 15))
        factory = PeriodFromTransactionFactory(transaction, Grouping.YEAR)
        period = factory.create()
        assert isinstance(period, Year)
        assert period.start == datetime(2023, 1, 1, 0, 0)
        assert period.end == datetime(2023, 12, 31, 23, 59, 59, 999999)

    def test_invalid_grouping(self) -> None:
        """Test invalid grouping raises error."""
        transaction = self.MockTransaction(date(2023, 6, 15))
        factory = PeriodFromTransactionFactory(transaction, Grouping.DAY)
        with pytest.raises(ValueError, match="Invalid grouping"):
            factory.create()


class TestPeriodSchema:
    """Tests for the PeriodSchema Pydantic model."""

    def test_from_period(self) -> None:
        """Test creating PeriodSchema from a Period instance."""
        period = Month.from_month_and_year(3, 2023)
        schema = PeriodSchema.from_period(period)
        assert schema.start == period.start
        assert schema.end == period.end
        assert schema.grouping == Grouping.MONTH
        assert schema.value == "03/2023"

    def test_to_period_month(self) -> None:
        """Test converting PeriodSchema to Month."""
        schema = PeriodSchema(
            start=datetime(2023, 3, 1),
            end=datetime(2023, 3, 31, 23, 59, 59, 999999),
            grouping=Grouping.MONTH,
            value="03/2023",
        )
        period = schema.to_period()
        assert isinstance(period, Month)

    def test_to_period_quarter(self) -> None:
        """Test converting PeriodSchema to Quarter."""
        schema = PeriodSchema(
            start=datetime(2023, 4, 1),
            end=datetime(2023, 6, 30, 23, 59, 59, 999999),
            grouping=Grouping.QUARTER,
            value="04/2023 - 06/2023",
        )
        period = schema.to_period()
        assert isinstance(period, Quarter)

    def test_to_period_year(self) -> None:
        """Test converting PeriodSchema to Year."""
        schema = PeriodSchema(
            start=datetime(2023, 1, 1),
            end=datetime(2023, 12, 31, 23, 59, 59, 999999),
            grouping=Grouping.YEAR,
            value="2023 - 2023",
        )
        period = schema.to_period()
        assert isinstance(period, Year)

    def test_model_serialization(self) -> None:
        """Test that PeriodSchema can be serialized to JSON."""
        period = Month.from_month_and_year(3, 2023)
        schema = PeriodSchema.from_period(period)
        json_data = schema.model_dump_json()
        assert "03/2023" in json_data
        assert "MONTH" in json_data


class TestPeriodWithDateInput:
    """Tests for Period classes accepting date (not datetime) inputs."""

    def test_period_with_date_input(self) -> None:
        """Test Period can be initialized with date objects."""
        period = Period(
            start=date(2023, 1, 1), end=date(2023, 1, 31), grouping=Grouping.MONTH
        )
        assert period.start == datetime(2023, 1, 1, 0, 0)
        assert period.end == datetime(2023, 1, 31, 23, 59, 59, 999999)

    def test_month_with_date_input(self) -> None:
        """Test Month can be initialized with date objects."""
        month = Month(start=date(2023, 2, 1), end=date(2023, 2, 28))
        assert month.start == datetime(2023, 2, 1, 0, 0)
        assert month.end == datetime(2023, 2, 28, 23, 59, 59, 999999)

    def test_quarter_from_date(self) -> None:
        """Test Quarter.from_date works with date objects."""
        quarter = Quarter.from_date(date(2023, 5, 15))
        assert quarter.quarter_nr == 2
        assert quarter.start == datetime(2023, 4, 1, 0, 0)
        assert quarter.end == datetime(2023, 6, 30, 23, 59, 59, 999999)

    def test_year_with_date_input(self) -> None:
        """Test Year can be initialized with date objects."""
        year = Year(start=date(2023, 1, 1), end=date(2023, 12, 31))
        assert year.start == datetime(2023, 1, 1, 0, 0)
        assert year.end == datetime(2023, 12, 31, 23, 59, 59, 999999)
