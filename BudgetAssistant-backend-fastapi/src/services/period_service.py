"""Period service for date range utilities."""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional

from schemas import DateRangeShortcut, ResolvedDateRange


class PeriodService:
    """Service for period/date range operations."""

    def resolve_start_end_date_shortcut(
        self,
        shortcut: DateRangeShortcut,
    ) -> ResolvedDateRange:
        """Resolve a date range shortcut to actual start and end dates."""
        now = datetime.now()

        if shortcut == DateRangeShortcut.CURRENT_MONTH:
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # End of current month
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(
                    seconds=1
                )
            else:
                end = start.replace(month=start.month + 1, day=1) - timedelta(seconds=1)

        elif shortcut == DateRangeShortcut.PREVIOUS_MONTH:
            first_of_current = now.replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end = first_of_current - timedelta(seconds=1)
            start = end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        elif shortcut == DateRangeShortcut.CURRENT_QUARTER:
            quarter = (now.month - 1) // 3
            start_month = quarter * 3 + 1
            start = now.replace(
                month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            # End of quarter
            end_month = start_month + 2
            if end_month > 12:
                end = datetime(now.year + 1, 1, 1) - timedelta(seconds=1)
            else:
                end = datetime(now.year, end_month + 1, 1) - timedelta(seconds=1)

        elif shortcut == DateRangeShortcut.PREVIOUS_QUARTER:
            quarter = (now.month - 1) // 3
            if quarter == 0:
                # Previous quarter is Q4 of previous year
                start = datetime(now.year - 1, 10, 1)
                end = datetime(now.year, 1, 1) - timedelta(seconds=1)
            else:
                start_month = (quarter - 1) * 3 + 1
                start = datetime(now.year, start_month, 1)
                end_month = start_month + 2
                end = datetime(now.year, end_month + 1, 1) - timedelta(seconds=1)

        elif shortcut == DateRangeShortcut.CURRENT_YEAR:
            start = now.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end = now.replace(
                month=12, day=31, hour=23, minute=59, second=59, microsecond=999999
            )

        elif shortcut == DateRangeShortcut.PREVIOUS_YEAR:
            start = datetime(now.year - 1, 1, 1)
            end = datetime(now.year, 1, 1) - timedelta(seconds=1)

        elif shortcut == DateRangeShortcut.ALL:
            # Return a very wide range
            start = datetime(2000, 1, 1)
            end = now.replace(hour=23, minute=59, second=59, microsecond=999999)

        else:
            # Default to current month
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1, day=1) - timedelta(
                    seconds=1
                )
            else:
                end = start.replace(month=start.month + 1, day=1) - timedelta(seconds=1)

        return ResolvedDateRange(
            start=start,
            end=end,
            shortcut=shortcut.value,
        )

    def get_period_boundaries(
        self,
        date: datetime,
        grouping: str,
    ) -> tuple[datetime, datetime]:
        """Get the start and end of a period containing the given date."""
        if grouping.upper() == "MONTH":
            start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start.month == 12:
                end = start.replace(year=start.year + 1, month=1) - timedelta(seconds=1)
            else:
                end = start.replace(month=start.month + 1) - timedelta(seconds=1)

        elif grouping.upper() == "QUARTER":
            quarter = (date.month - 1) // 3
            start_month = quarter * 3 + 1
            start = date.replace(
                month=start_month, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end_month = start_month + 2
            if end_month >= 12:
                end = datetime(date.year + 1, 1, 1) - timedelta(seconds=1)
            else:
                end = datetime(date.year, end_month + 1, 1) - timedelta(seconds=1)

        elif grouping.upper() == "YEAR":
            start = date.replace(
                month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end = date.replace(
                month=12, day=31, hour=23, minute=59, second=59, microsecond=999999
            )

        else:
            # Default to month
            return self.get_period_boundaries(date, "MONTH")

        return start, end

    def format_period(
        self,
        date: datetime,
        grouping: str,
    ) -> str:
        """Format a period as a string."""
        if grouping.upper() == "MONTH":
            return f"{date.year}-{date.month:02d}"
        elif grouping.upper() == "QUARTER":
            quarter = (date.month - 1) // 3 + 1
            return f"{date.year}-Q{quarter}"
        elif grouping.upper() == "YEAR":
            return str(date.year)
        else:
            return f"{date.year}-{date.month:02d}"


# Singleton instance
period_service = PeriodService()

