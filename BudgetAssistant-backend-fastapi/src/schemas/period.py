"""Period classes for date range handling with grouping functionality.

This module provides Period classes that handle date ranges with different groupings
(month, quarter, year). These are used for analysis and reporting features.
"""

import dataclasses
import json
from datetime import date, datetime, timedelta
from typing import TYPE_CHECKING, ClassVar, Dict, Optional, Union

import arrow
from arrow import Arrow
from pydantic import BaseModel, ConfigDict

from schemas.common import Grouping

if TYPE_CHECKING:
    from models import Transaction


def get_arrow(_datetime: Union[datetime, date]) -> Arrow:
    """Convert a datetime or date to an Arrow object."""
    return arrow.get(_datetime.year, _datetime.month, _datetime.day)


class Period:
    """Represents a time period with start, end, grouping and formatted value.

    The Period class provides comparison, hashing, and serialization functionality
    for time periods that can be grouped by month, quarter, or year.
    """

    def __init__(
        self,
        start: Union[datetime, date],
        end: Union[datetime, date],
        grouping: Grouping,
    ):
        """Initialize a Period.

        Args:
            start: The start datetime/date of the period.
            end: The end datetime/date of the period.
            grouping: The grouping type (MONTH, QUARTER, YEAR).
        """
        # Convert to date if datetime is passed
        if isinstance(start, datetime):
            start = start.date()
        if isinstance(end, datetime):
            end = end.date()

        self.start: date = arrow.get(start.year, start.month, start.day).floor("day").date()
        self.end: date = arrow.get(end.year, end.month, end.day).ceil("day").date()
        self.grouping = grouping
        self.value = self.init_value(start, end, grouping)

    @staticmethod
    def from_transaction(transaction: "Transaction", grouping: Grouping) -> "Period":
        """Create a Period from a transaction's booking date."""
        return PeriodFromTransactionFactory(transaction, grouping).create()

    def init_value(
        self,
        start: Union[datetime, date],
        end: Union[datetime, date],
        grouping: Grouping,
    ) -> str:
        """Initialize the formatted value string for this period."""
        return PeriodValueFormatter().run(start, end, grouping)

    def to_json(self) -> str:
        """Serialize the Period to a JSON string."""
        data = {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "grouping": self.grouping.value,
            "value": self.value,
        }
        return json.dumps(data)

    @staticmethod
    def from_json(json_str: str) -> "Period":
        """Deserialize a Period from a JSON string."""
        data = json.loads(json_str)
        start = date.fromisoformat(data["start"])
        end = date.fromisoformat(data["end"])
        grouping = Grouping(data["grouping"].upper())
        return Period(start, end, grouping)

    def next(self) -> "Period":
        """Get the next period. Subclasses should implement this."""
        raise NotImplementedError("Subclasses should implement this!")

    def previous(self) -> "Period":
        """Get the previous period. Subclasses should implement this."""
        raise NotImplementedError("Subclasses should implement this!")

    def __lt__(self, other: "Period") -> bool:
        """Less than comparison based on start date."""
        return self.start < other.start

    def __gt__(self, other: "Period") -> bool:
        """Greater than comparison based on start date."""
        return self.start > other.start

    def __eq__(self, other: object) -> bool:
        """Equality comparison based on all attributes."""
        if not isinstance(other, Period):
            return NotImplemented
        # Check if all attributes are not None, else raise ValueError
        if self.start is None or self.end is None or self.grouping is None or self.value is None:
            raise ValueError("Attributes of Period should not be None")
        return (
            self.start == other.start
            and self.end == other.end
            and self.grouping == other.grouping
            and self.value == other.value
        )

    def __hash__(self) -> int:
        """Hash based on all attributes."""
        # Check if all attributes are not None, else raise ValueError
        if self.start is None or self.end is None or self.grouping is None or self.value is None:
            raise ValueError("Attributes of Period should not be None")
        return hash((self.start, self.end, self.grouping, self.value))

    def __str__(self) -> str:
        """String representation returns the formatted value."""
        return self.value

    def __repr__(self) -> str:
        """Repr returns the formatted value."""
        return self.value


class PeriodFromTransactionFactory:
    """Factory for creating Period instances from transactions."""

    def __init__(self, transaction: "Transaction", grouping: Grouping):
        """Initialize the factory.

        Args:
            transaction: The transaction to create a period from.
            grouping: The grouping type for the period.
        """
        self.transaction = transaction
        self.grouping = grouping

    def create(self) -> Period:
        """Create a Period based on the transaction's booking date and grouping."""
        if self.grouping == Grouping.MONTH:
            return self.with_grouping_is_month()
        elif self.grouping == Grouping.QUARTER:
            return self.with_grouping_is_quarter()
        elif self.grouping == Grouping.YEAR:
            return self.with_grouping_is_year()
        else:
            raise ValueError("Invalid grouping")

    def with_grouping_is_month(self) -> "Month":
        """Create a Month period from the transaction."""
        bookingdate = self.transaction.booking_date
        start_of_month = bookingdate.replace(day=1)
        last_day_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return Month(start_of_month, last_day_of_month)

    def with_grouping_is_quarter(self) -> "Quarter":
        """Create a Quarter period from the transaction."""
        return Quarter.from_date(self.transaction.booking_date)

    def with_grouping_is_year(self) -> "Year":
        """Create a Year period from the transaction."""
        start_of_year = self.transaction.booking_date.replace(month=1, day=1)
        end_of_year = self.transaction.booking_date.replace(month=12, day=31)
        return Year(start_of_year, end_of_year)


class Quarter(Period):
    """A Period representing a calendar quarter."""

    @dataclasses.dataclass(frozen=True)
    class QuarterConstant:
        """Constant definition for a quarter."""

        quarter_nr: int
        start_day: int
        start_month: int
        end_day: int
        end_month: int

        def to_quarter(self, year: int) -> "Quarter":
            """Convert to a Quarter instance for a specific year."""
            return Quarter(
                self.quarter_nr,
                date(year, self.start_month, self.start_day),
                date(year, self.end_month, self.end_day),
            )

    Q1 = QuarterConstant(quarter_nr=1, start_day=1, start_month=1, end_day=31, end_month=3)
    Q2 = QuarterConstant(quarter_nr=2, start_day=1, start_month=4, end_day=30, end_month=6)
    Q3 = QuarterConstant(quarter_nr=3, start_day=1, start_month=7, end_day=30, end_month=9)
    Q4 = QuarterConstant(quarter_nr=4, start_day=1, start_month=10, end_day=31, end_month=12)

    MONTH_TO_QUARTER_DICT: ClassVar[Optional[Dict[int, QuarterConstant]]] = None
    QUARTER_NR_TO_QUARTER_DICT: ClassVar[Dict[int, QuarterConstant]] = {
        const.quarter_nr: const for const in [Q1, Q2, Q3, Q4]
    }

    @classmethod
    def _create_month_to_quarter_dict(cls) -> None:
        """Create the mapping from month number to quarter constant."""

        def create_dict(
            const: "Quarter.QuarterConstant",
        ) -> Dict[int, "Quarter.QuarterConstant"]:
            # Range of months from const.start_month to const.end_month
            return {month: const for month in range(const.start_month, const.end_month + 1)}

        quarters = [cls.Q1, cls.Q2, cls.Q3, cls.Q4]
        # Create a dict for every quarter constant and merge them
        result = {month: const for quarter in quarters for month, const in create_dict(quarter).items()}
        # Ensure that the len of result is 12
        if len(result) != 12:
            raise ValueError("The length of the result should be 12")
        # Ensure that every month is in the dict
        if set(result.keys()) != set(range(1, 13)):
            raise ValueError("The keys of the result should be the months from 1 to 12")
        cls.MONTH_TO_QUARTER_DICT = result

    def __init__(self, quarter_nr: int, start: Union[datetime, date], end: Union[datetime, date]):
        """Initialize a Quarter.

        Args:
            quarter_nr: The quarter number (1-4).
            start: The start date of the quarter.
            end: The end date of the quarter.
        """
        if Quarter.MONTH_TO_QUARTER_DICT is None:
            Quarter._create_month_to_quarter_dict()
        super().__init__(start, end, Grouping.QUARTER)
        self.quarter_nr = quarter_nr

    @staticmethod
    def from_date(dt: Union[datetime, date]) -> "Quarter":
        """Create a Quarter from a date."""
        if Quarter.MONTH_TO_QUARTER_DICT is None:
            Quarter._create_month_to_quarter_dict()
        return Quarter.MONTH_TO_QUARTER_DICT[dt.month].to_quarter(dt.year)

    def get_previous(self) -> "Quarter":
        """Get the previous quarter."""
        if self.quarter_nr > 1:
            return Quarter.QUARTER_NR_TO_QUARTER_DICT[self.quarter_nr - 1].to_quarter(self.start.year)
        else:
            return Quarter.QUARTER_NR_TO_QUARTER_DICT[4].to_quarter(self.start.year - 1)

    def get_next(self) -> "Quarter":
        """Get the next quarter."""
        if self.quarter_nr < 4:
            return Quarter.QUARTER_NR_TO_QUARTER_DICT[self.quarter_nr + 1].to_quarter(self.start.year)
        else:
            return Quarter.QUARTER_NR_TO_QUARTER_DICT[1].to_quarter(self.start.year + 1)

    @staticmethod
    def from_quarter_nr_and_year(quarter_number: int, year: int) -> "Quarter":
        """Create a Quarter from a quarter number and year."""
        return Quarter.QUARTER_NR_TO_QUARTER_DICT[quarter_number].to_quarter(year)


# Initialize the month to quarter dict
Quarter._create_month_to_quarter_dict()


class Month(Period):
    """A Period representing a calendar month."""

    def __init__(self, start: Union[datetime, date], end: Union[datetime, date]):
        """Initialize a Month.

        Args:
            start: The start datetime/date of the month.
            end: The end datetime/date of the month.
        """
        super().__init__(start, end, Grouping.MONTH)

    def next(self) -> "Month":
        """Get the next month."""
        arr = get_arrow(self.start).shift(months=1)
        next_start = arr.floor("month").date()
        next_end = arr.ceil("month").date()
        return Month(next_start, next_end)

    def previous(self) -> "Month":
        """Get the previous month."""
        arr = get_arrow(self.start).shift(months=-1)
        previous_start = arr.floor("month").date()
        previous_end = arr.ceil("month").date()
        return Month(previous_start, previous_end)

    def _get_previous(self, d: date) -> date:
        """Get the previous month's equivalent date."""
        if d.month == 1:
            return d.replace(month=12, year=d.year - 1)
        else:
            return d.replace(month=d.month - 1)

    def _get_next(self, d: date) -> date:
        """Get the next month's equivalent date."""
        if d.month == 12:
            return d.replace(month=1, year=d.year + 1)
        else:
            return d.replace(month=d.month + 1)

    @staticmethod
    def from_month_and_year(month: int, year: int) -> "Month":
        """Create a Month from a month number and year."""
        start = date(year, month, 1)
        end = (datetime(year, month, 1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return Month(start, end.date() if isinstance(end, datetime) else end)


class Year(Period):
    """A Period representing a calendar year."""

    def __init__(self, start: Union[datetime, date], end: Union[datetime, date]):
        """Initialize a Year.

        Args:
            start: The start datetime/date of the year.
            end: The end datetime/date of the year.
        """
        super().__init__(start, end, Grouping.YEAR)

    def next(self) -> "Year":
        """Get the next year."""
        next_start = self._get_next(self.start)
        next_end = self._get_next(self.end)
        return Year(next_start, next_end)

    def previous(self) -> "Year":
        """Get the previous year."""
        previous_start = self._get_previous(self.start)
        previous_end = self._get_previous(self.end)
        return Year(previous_start, previous_end)

    def _get_previous(self, d: date) -> date:
        """Get the previous year's equivalent date."""
        return d.replace(year=d.year - 1)

    def _get_next(self, d: date) -> date:
        """Get the next year's equivalent date."""
        return d.replace(year=d.year + 1)

    @staticmethod
    def from_year(year: int) -> "Year":
        """Create a Year from a year number."""
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        return Year(start, end)


class PeriodValueFormatter:
    """Formatter for period value strings."""

    def run(
        self,
        start: Union[datetime, date],
        end: Union[datetime, date],
        grouping: Grouping,
    ) -> str:
        """Format a period as a string based on grouping.

        Args:
            start: The start datetime/date.
            end: The end datetime/date.
            grouping: The grouping type.

        Returns:
            A formatted string representation of the period.
        """
        if grouping == Grouping.MONTH:
            return start.strftime("%m/%Y")
        elif grouping == Grouping.QUARTER:
            return f"{start.strftime('%m/%Y')} - {end.strftime('%m/%Y')}"
        elif grouping == Grouping.YEAR:
            return f"{start.strftime('%Y')} - {end.strftime('%Y')}"
        else:
            raise ValueError("Unexpected value for grouping")


class PeriodSchema(BaseModel):
    """Pydantic schema for Period serialization."""

    model_config = ConfigDict(from_attributes=True)

    start: date
    end: date
    grouping: Grouping
    value: str

    @classmethod
    def from_period(cls, period: Period) -> "PeriodSchema":
        """Create a PeriodSchema from a Period instance."""
        return cls(
            start=period.start,
            end=period.end,
            grouping=period.grouping,
            value=period.value,
        )

    def to_period(self) -> Period:
        """Convert to a Period instance."""
        if self.grouping == Grouping.MONTH:
            return Month(self.start, self.end)
        elif self.grouping == Grouping.QUARTER:
            return Quarter.from_date(self.start)
        elif self.grouping == Grouping.YEAR:
            return Year(self.start, self.end)
        else:
            return Period(self.start, self.end, self.grouping)
