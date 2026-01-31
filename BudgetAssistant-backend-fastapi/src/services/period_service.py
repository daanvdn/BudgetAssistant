"""Period service for date range utilities."""

from datetime import datetime

from schemas import DateRangeShortcut, Grouping, ResolvedDateRange
from schemas.period import Month, Period, Quarter, Year


class PeriodService:
    """Service for period/date range operations."""

    def resolve_start_end_date_shortcut(
        self,
        shortcut: DateRangeShortcut,
    ) -> ResolvedDateRange:
        """Resolve a date range shortcut to actual start and end dates."""
        now = datetime.now()

        if shortcut == DateRangeShortcut.CURRENT_MONTH:
            period = Month.from_month_and_year(now.month, now.year)
            start = period.start
            end = period.end

        elif shortcut == DateRangeShortcut.PREVIOUS_MONTH:
            current_month = Month.from_month_and_year(now.month, now.year)
            period = current_month.previous()
            start = period.start
            end = period.end

        elif shortcut == DateRangeShortcut.CURRENT_QUARTER:
            period = Quarter.from_date(now)
            start = period.start
            end = period.end

        elif shortcut == DateRangeShortcut.PREVIOUS_QUARTER:
            current_quarter = Quarter.from_date(now)
            period = current_quarter.get_previous()
            start = period.start
            end = period.end

        elif shortcut == DateRangeShortcut.CURRENT_YEAR:
            period = Year.from_year(now.year)
            start = period.start
            end = period.end

        elif shortcut == DateRangeShortcut.PREVIOUS_YEAR:
            period = Year.from_year(now.year - 1)
            start = period.start
            end = period.end

        elif shortcut == DateRangeShortcut.ALL:
            # Return a very wide range
            start = datetime(2000, 1, 1)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        else:
            # Default to current month
            period = Month.from_month_and_year(now.month, now.year)
            start = period.start
            end = period.end

        return ResolvedDateRange(
            start=start,
            end=end,
            shortcut=shortcut.value,
        )

    def get_period_for_date(
        self,
        date: datetime,
        grouping: Grouping,
    ) -> Period:
        """Get a Period instance for a date based on grouping."""
        if grouping == Grouping.MONTH:
            return Month.from_month_and_year(date.month, date.year)
        elif grouping == Grouping.QUARTER:
            return Quarter.from_date(date)
        elif grouping == Grouping.YEAR:
            return Year.from_year(date.year)
        else:
            # Default to month
            return Month.from_month_and_year(date.month, date.year)

    def get_period_boundaries(
        self,
        date: datetime,
        grouping: str,
    ) -> tuple[datetime, datetime]:
        """Get the start and end of a period containing the given date.

        Uses Period classes for consistent period calculation.
        """
        # Convert string grouping to Grouping enum
        try:
            grouping_enum = Grouping(grouping.upper())
        except ValueError:
            grouping_enum = Grouping.MONTH

        period = self.get_period_for_date(date, grouping_enum)
        return period.start, period.end

    def format_period(
        self,
        date: datetime,
        grouping: str,
    ) -> str:
        """Format a period as a string.

        Uses Period classes for consistent formatting.
        """
        # Convert string grouping to Grouping enum
        try:
            grouping_enum = Grouping(grouping.upper())
        except ValueError:
            grouping_enum = Grouping.MONTH

        period = self.get_period_for_date(date, grouping_enum)
        return period.value


# Singleton instance
period_service = PeriodService()
