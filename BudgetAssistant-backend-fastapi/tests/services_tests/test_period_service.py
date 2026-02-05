from datetime import date

from schemas import DateRangeShortcut
from services.period_service import PeriodService


class TestPeriodService:
    """Tests for PeriodService."""

    def test_resolve_current_month(self):
        """Test resolving current month shortcut."""
        service = PeriodService()
        result = service.resolve_start_end_date_shortcut(DateRangeShortcut.CURRENT_MONTH)

        now = date.today()
        assert result.start.month == now.month
        assert result.start.year == now.year
        assert result.start.day == 1
        assert result.shortcut == "current month"

    def test_resolve_previous_month(self):
        """Test resolving previous month shortcut."""
        service = PeriodService()
        result = service.resolve_start_end_date_shortcut(DateRangeShortcut.PREVIOUS_MONTH)

        now = date.today()
        if now.month == 1:
            expected_month = 12
            expected_year = now.year - 1
        else:
            expected_month = now.month - 1
            expected_year = now.year

        assert result.start.month == expected_month
        assert result.start.year == expected_year
        assert result.shortcut == "previous month"

    def test_resolve_current_year(self):
        """Test resolving current year shortcut."""
        service = PeriodService()
        result = service.resolve_start_end_date_shortcut(DateRangeShortcut.CURRENT_YEAR)

        now = date.today()
        assert result.start.year == now.year
        assert result.start.month == 1
        assert result.start.day == 1
        assert result.end.month == 12
        assert result.end.day == 31
        assert result.shortcut == "current year"

    def test_resolve_previous_year(self):
        """Test resolving previous year shortcut."""
        service = PeriodService()
        result = service.resolve_start_end_date_shortcut(DateRangeShortcut.PREVIOUS_YEAR)

        now = date.today()
        assert result.start.year == now.year - 1
        assert result.start.month == 1
        assert result.start.day == 1
        assert result.shortcut == "previous year"

    def test_resolve_all(self):
        """Test resolving 'all' shortcut."""
        service = PeriodService()
        result = service.resolve_start_end_date_shortcut(DateRangeShortcut.ALL)

        assert result.start.year == 2000
        assert result.shortcut == "all"

    def test_get_period_boundaries_month(self):
        """Test getting period boundaries for month grouping."""
        service = PeriodService()
        test_date = date(2023, 5, 15)

        start, end = service.get_period_boundaries(test_date, "MONTH")

        assert start.year == 2023
        assert start.month == 5
        assert start.day == 1
        assert end.month == 5
        assert end.day == 31

    def test_get_period_boundaries_quarter(self):
        """Test getting period boundaries for quarter grouping."""
        service = PeriodService()
        test_date = date(2023, 5, 15)  # Q2

        start, end = service.get_period_boundaries(test_date, "QUARTER")

        assert start.year == 2023
        assert start.month == 4  # Q2 starts in April
        assert start.day == 1

    def test_get_period_boundaries_year(self):
        """Test getting period boundaries for year grouping."""
        service = PeriodService()
        test_date = date(2023, 5, 15)

        start, end = service.get_period_boundaries(test_date, "YEAR")

        assert start.year == 2023
        assert start.month == 1
        assert start.day == 1
        assert end.month == 12
        assert end.day == 31

    def test_format_period_month(self):
        """Test formatting period for month grouping.

        Uses Period class format: MM/YYYY (matching Django backend).
        """
        service = PeriodService()
        test_date = date(2023, 5, 15)

        result = service.format_period(test_date, "MONTH")

        assert result == "05/2023"

    def test_format_period_quarter(self):
        """Test formatting period for quarter grouping.

        Uses Period class format: MM/YYYY - MM/YYYY (matching Django backend).
        """
        service = PeriodService()

        # Q1
        assert service.format_period(date(2023, 2, 15), "QUARTER") == "01/2023 - 03/2023"
        # Q2
        assert service.format_period(date(2023, 5, 15), "QUARTER") == "04/2023 - 06/2023"
        # Q3
        assert service.format_period(date(2023, 8, 15), "QUARTER") == "07/2023 - 09/2023"
        # Q4
        assert service.format_period(date(2023, 11, 15), "QUARTER") == "10/2023 - 12/2023"

    def test_format_period_year(self):
        """Test formatting period for year grouping.

        Uses Period class format: YYYY - YYYY (matching Django backend).
        """
        service = PeriodService()
        test_date = date(2023, 5, 15)

        result = service.format_period(test_date, "YEAR")

        assert result == "2023 - 2023"
