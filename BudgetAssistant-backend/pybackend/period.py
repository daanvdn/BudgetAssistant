import dataclasses
import json
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict

import arrow
import jsonpickle
from arrow import Arrow
from enumfields.drf import EnumField
from enumfields.enums import ChoicesEnum
from rest_framework.fields import CharField
from rest_framework.serializers import Serializer, DateTimeField


def get_arrow(_datetime:datetime) -> Arrow:
    return arrow.get(_datetime.year, _datetime.month, _datetime.day)
class Grouping(str, ChoicesEnum):
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"

    @staticmethod
    def from_string_value(string_value):
        for grouping in Grouping:
            if grouping.value == string_value.lower():
                return grouping
        raise ValueError("Invalid string value for Grouping")


class Period:

    def __init__(self, start:datetime, end:datetime, grouping):
        self.start = arrow.get(start.year, start.month, start.day).floor('day').datetime
        #remove timezone info
        self.start = self.start.replace(tzinfo=None)
        self.end = arrow.get(end.year, end.month, end.day).ceil('day').datetime
        self.end = self.end.replace(tzinfo=None)
        self.grouping = grouping
        self.value = self.init_value(start, end, grouping)

    @staticmethod
    def at_start_of_day(date):
        return datetime.combine(date, datetime.min.time())

    @staticmethod
    def at_end_of_day(date):
        return datetime.combine(date, datetime.max.time())

    @staticmethod
    def from_transaction(transaction: 'Transaction', grouping: Grouping):
        return PeriodFromTransactionFactory(transaction, grouping).create()

    def init_value(self, start, end, grouping):
        return PeriodValueFormatter().run(start, end, grouping)

    def to_json(self):
        #I want to pickle the grouping enum to a string

        j = jsonpickle.encode(self, unpicklable=False)
        j = json.loads(j)
        j['grouping'] = self.grouping.value
        return json.dumps(j)

    @staticmethod
    def from_json(json_str):
        a_dict = jsonpickle.decode(json_str, classes=[Period])
        start_ = a_dict['start']
        #convert start_ to datetime
        start_ = datetime.fromisoformat(start_)
        end_ = a_dict['end']
        #convert end_ to datetime
        end_ = datetime.fromisoformat(end_)
        grouping = Grouping.from_string_value(a_dict['grouping'])
        return Period(start_, end_, grouping)
    def next(self):
        raise NotImplementedError("Subclasses should implement this!")

    def previous(self):
        raise NotImplementedError("Subclasses should implement this!")

    def __lt__(self, other):
        return self.start < other.start

    def __gt__(self, other):
        return self.start > other.start

    def __eq__(self, other):
        #check if all attributes are not None, else raise ValueError
        if self.start is None or self.end is None or self.grouping is None or self.value is None:
            raise ValueError("Attributes of Period should not be None")
        return self.start == other.start and self.end == other.end and self.grouping == other.grouping and self.value == other.value

    def __hash__(self):
        #check if all attributes are not None, else raise ValueError
        if self.start is None or self.end is None or self.grouping is None or self.value is None:
            raise ValueError("Attributes of Period should not be None")
        return hash((self.start, self.end, self.grouping, self.value))

    def __str__(self):
        return self.value

    def __repr__(self):
        return self.value



class PeriodFromTransactionFactory:
    def __init__(self, transaction: 'Transaction', grouping: Grouping):
        self.transaction = transaction
        self.grouping = grouping

    def create(self):
        if self.grouping == Grouping.MONTH:
            return self.with_grouping_is_month()
        elif self.grouping == Grouping.QUARTER:
            return self.with_grouping_is_quarter()
        elif self.grouping == Grouping.YEAR:
            return self.with_grouping_is_year()
        else:
            raise ValueError("Invalid grouping")

    def with_grouping_is_month(self) -> Period:
        bookingdate = self.transaction.booking_date
        start_of_month = bookingdate.replace(day=1)
        last_day_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return Month(start_of_month, last_day_of_month)

    def with_grouping_is_quarter(self) -> Period:
        quarter = Quarter.from_date(self.transaction.booking_date)
        return quarter
    def with_grouping_is_year(self) -> Period:
        start_of_year = self.transaction.booking_date.replace(month=1, day=1)
        end_of_year = self.transaction.booking_date.replace(month=12, day=31)
        return Year(start_of_year, end_of_year)


class Quarter(Period):

    @dataclasses.dataclass(frozen=True)
    class QuarterConstant:
        quarter_nr: int
        start_day: int
        start_month: int
        end_day: int
        end_month: int

        def to_quarter(self, year:int) -> 'Quarter':
            return Quarter(self.quarter_nr, datetime(year, self.start_month, self.start_day), datetime(year, self.end_month, self.end_day))

    Q1 = QuarterConstant(quarter_nr=1, start_day=1, start_month=1, end_day=31, end_month=3)
    Q2 = QuarterConstant(quarter_nr=2, start_day=1, start_month=4, end_day=30, end_month=6)
    Q3 = QuarterConstant(quarter_nr=3, start_day=1, start_month=7, end_day=30, end_month=9)
    Q4 = QuarterConstant(quarter_nr=4, start_day=1, start_month=10, end_day=31, end_month=12)

    MONTH_TO_QUARTER_DICT: Dict[int, QuarterConstant] = None
    QUARTER_NR_TO_QUARTER_DICT: Dict[int, QuarterConstant] = {const.quarter_nr: const for const in [Q1, Q2, Q3, Q4]}


    @classmethod
    def _create_month_to_quarter_dict(cls) -> None:

        def create_dict(const: Quarter.QuarterConstant):
            #range of months from const.start_month to const.end_month
            return {month: const for month in range(const.start_month, const.end_month + 1)}
        quarters =  [cls.Q1, cls.Q2, cls.Q3, cls.Q4]
        #create a dict for every quarterconstant and merge them
        result = {month: const for quarter in quarters for month, const in create_dict(quarter).items()}
        #ensure that the len of result is 12, ensure that every month is in the dict, ensure that every month is in
        # the dict only once, ensure that every QuarterConstant is in the dict 3 times
        if not (len(result) == 12):
            raise ValueError("The length of the result should be 12")
        if not (set(result.keys()) == set(range(1, 13))):
            raise ValueError("The keys of the result should be the months from 1 to 12")
        cls.MONTH_TO_QUARTER_DICT = result


    def __init__(self, quarter_nr, start, end):
        if Quarter.MONTH_TO_QUARTER_DICT is None:
            Quarter._create_month_to_quarter_dict()
        super().__init__(start, end, Grouping.QUARTER)
        self.quarter_nr = quarter_nr


    @staticmethod
    def from_date(date) -> 'Quarter':

        return Quarter.MONTH_TO_QUARTER_DICT[date.month].to_quarter(date.year)

    def get_previous(self) -> 'Quarter':
        if self.quarter_nr >1:
            return Quarter.QUARTER_NR_TO_QUARTER_DICT[self.quarter_nr-1].to_quarter(self.start.year)
        else:
            return Quarter.QUARTER_NR_TO_QUARTER_DICT[4].to_quarter(self.start.year-1)


    def get_next(self) -> 'Quarter':
        if self.quarter_nr < 4:
            return Quarter.QUARTER_NR_TO_QUARTER_DICT[self.quarter_nr+1].to_quarter(self.start.year)
        else:
            return Quarter.QUARTER_NR_TO_QUARTER_DICT[1].to_quarter(self.start.year+1)

    @staticmethod
    def from_quarter_nr_and_year(quarter_number: int, year: int) -> 'Quarter':
        return Quarter.QUARTER_NR_TO_QUARTER_DICT[quarter_number].to_quarter(year)

Quarter._create_month_to_quarter_dict()

class Month(Period):
    def __init__(self, start:datetime, end:datetime):
        super().__init__(start, end, Grouping.MONTH)

    def next(self) -> 'Month':
        arrow = get_arrow(self.start).shift(months=1)
        next_start = arrow.floor('month').datetime
        next_end = arrow.ceil('month').datetime
        return Month(next_start, next_end)

    def previous(self) -> 'Month':
        arrow = get_arrow(self.start).shift(months=-1)
        previous_start = arrow.floor('month').datetime
        previous_end = arrow.ceil('month').datetime
        return Month(previous_start, previous_end)

    def _get_previous(self, date) -> datetime:
        if date.month == 1:
            return date.replace(month=12, year=date.year - 1)
        else:
            return date.replace(month=date.month - 1)

    def _get_next(self, date) -> datetime:
        if date.month == 12:
            return date.replace(month=1, year=date.year + 1)
        else:
            return date.replace(month=date.month + 1)

    @staticmethod
    def from_month_and_year(month: int, year: int):
        start = datetime(year, month, 1)
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return Month(start, end)


class Year(Period):
    def __init__(self, start, end):
        super().__init__(start, end, Grouping.YEAR)

    def next(self) -> 'Year':
        next_start = self._get_next(self.start)
        next_end = self._get_next(self.end)
        return Year(next_start, next_end)

    def previous(self) -> 'Year':
        previous_start = self._get_previous(self.start)
        previous_end = self._get_previous(self.end)
        return Year(previous_start, previous_end)

    def _get_previous(self, date) -> datetime:
        return date.replace(year=date.year - 1)

    def _get_next(self, date) -> datetime:
        return date.replace(year=date.year + 1)

    @staticmethod
    def from_year(year: int) -> 'Year':
        start = datetime(year, 1, 1)
        end = datetime(year, 12, 31)
        return Year(start, end)


class PeriodValueFormatter:
    def run(self, start, end, grouping) -> str:
        if grouping == Grouping.MONTH:
            return start.strftime("%m/%Y")
        elif grouping == Grouping.QUARTER:
            return f"{start.strftime('%m/%Y')} - {end.strftime('%m/%Y')}"
        elif grouping == Grouping.YEAR:
            return f"{start.strftime('%Y')} - {end.strftime('%Y')}"
        else:
            raise ValueError("Unexpected value for grouping")

class PeriodSerializer(Serializer):
    start = DateTimeField()
    end = DateTimeField()
    grouping = EnumField(Grouping)
    value = CharField()

    class Meta:
        model = Period
        fields = ['start', 'end', 'grouping', 'value']

    def create(self, validated_data):
        if 'value' in validated_data:
            del validated_data['value']
        period = Period(**validated_data)
        if period.grouping == Grouping.MONTH:
            return Month(period.start, period.end)
        elif period.grouping == Grouping.QUARTER:
            return Quarter.from_date(period.start)
        elif period.grouping == Grouping.YEAR:
            return Year(period.start, period.end)
        else:
            raise ValueError("Invalid grouping")
@dataclasses.dataclass
class ResolvedStartEndDateShortcut:
    start: datetime
    end: datetime

class ResolvedStartEndDateShortcutSerializer(Serializer):
    start = DateTimeField()
    end = DateTimeField()
    class Meta:
        fields = ['start', 'end']




class StartEndDateShortcut(Enum):
    CURRENT_MONTH = "current month"
    PREVIOUS_MONTH = "previous month"
    CURRENT_QUARTER = "current quarter"
    PREVIOUS_QUARTER = "previous quarter"
    CURRENT_YEAR = "current year"
    PREVIOUS_YEAR = "previous year"
    ALL = "all"

    @staticmethod
    def from_value_string(value_string: str) -> 'StartEndDateShortcut':
        for shortcut in StartEndDateShortcut:
            if shortcut.value == value_string:
                return shortcut
        raise ValueError("Invalid value string for StartEndDateShortcut")

    def resolve(self) -> ResolvedStartEndDateShortcut:
        return StartEndDateShortcutResolver(self).resolve()


class StartEndDateShortcutResolver:
    def __init__(self, start_end_date_shortcut: StartEndDateShortcut):
        self.now = datetime.now()
        self.start_end_date_shortcut = start_end_date_shortcut

    def resolve(self) -> ResolvedStartEndDateShortcut:
        if self.start_end_date_shortcut == StartEndDateShortcut.CURRENT_MONTH:
            return self.handle_current_month()
        elif self.start_end_date_shortcut == StartEndDateShortcut.PREVIOUS_MONTH:
            return self.handle_previous_month()
        elif self.start_end_date_shortcut == StartEndDateShortcut.CURRENT_QUARTER:
            return self.handle_current_quarter()
        elif self.start_end_date_shortcut == StartEndDateShortcut.PREVIOUS_QUARTER:
            return self.handle_previous_quarter()
        elif self.start_end_date_shortcut == StartEndDateShortcut.CURRENT_YEAR:
            return self.handle_current_year()
        elif self.start_end_date_shortcut == StartEndDateShortcut.PREVIOUS_YEAR:
            return self.handle_previous_year()
        elif self.start_end_date_shortcut == StartEndDateShortcut.ALL:
            return self.handle_all()
        else:
            raise ValueError("Invalid StartEndDateShortcut")

    def handle_current_month(self) -> ResolvedStartEndDateShortcut:
        start = self.now.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        return ResolvedStartEndDateShortcut(start, end)

    def handle_previous_month(self) -> ResolvedStartEndDateShortcut:
        start = (self.now.replace(day=1) - timedelta(days=1)).replace(day=1)
        end = self.now.replace(day=1) - timedelta(days=1)
        return ResolvedStartEndDateShortcut(start, end)

    def handle_current_quarter(self) -> ResolvedStartEndDateShortcut:
        quarter = self._get_quarter(self.now)
        return ResolvedStartEndDateShortcut(quarter['start'], quarter['end'])

    def handle_previous_quarter(self) -> ResolvedStartEndDateShortcut:
        quarter = self._get_quarter(self.now)
        previous_quarter = self._get_previous_quarter(quarter['start'])
        return ResolvedStartEndDateShortcut(previous_quarter['start'], previous_quarter['end'])

    def handle_current_year(self) -> ResolvedStartEndDateShortcut:
        start = self.now.replace(month=1, day=1)
        end = self.now.replace(month=12, day=31)
        return ResolvedStartEndDateShortcut(start, end)

    def handle_previous_year(self) -> ResolvedStartEndDateShortcut:
        start = self.now.replace(year=self.now.year - 1, month=1, day=1)
        end = self.now.replace(year=self.now.year - 1, month=12, day=31)
        return ResolvedStartEndDateShortcut(start, end)

    def handle_all(self) -> ResolvedStartEndDateShortcut:
        start = datetime(1970, 1, 1)
        end = self.now.replace(month=12, day=31)
        return ResolvedStartEndDateShortcut(start, end)

    def _get_quarter(self, date):
        quarter = (date.month - 1) // 3 + 1
        start_month = (quarter - 1) * 3 + 1
        start = date.replace(month=start_month, day=1)
        end = (start + timedelta(days=92)).replace(day=1) - timedelta(days=1)
        return {'start': start, 'end': end}

    def _get_previous_quarter(self, date):
        previous_quarter_start = (date - timedelta(days=92)).replace(day=1)
        previous_quarter_end = (previous_quarter_start + timedelta(days=92)).replace(day=1) - timedelta(days=1)
        return {'start': previous_quarter_start, 'end': previous_quarter_end}
