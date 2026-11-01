"""
Core calculation logic for AI credit usage analysis.
Calculate credit usage rate compared to time progress through the billing cycle.
Shows if you're using credits faster or slower than expected based on renewal date.
Default target day is the 1st of each month (renewal date).
"""

from datetime import datetime, timedelta
from typing import TypedDict


class ProgressResult(TypedDict):
    """Result of progress calculation."""

    current_percentage: float
    current_day: int
    target_day: int
    days_in_month: int
    days_since_renewal: int
    days_in_billing_cycle: int
    time_progress: float
    expected_percentage: float
    ratio: float
    difference_percentage: float
    projected_usage: float
    projected_remaining: float
    status: str


def ordinal_suffix(day: int) -> str:
    """
    Return the ordinal suffix for a given day number.

    Args:
        day: The day number (1-31)

    Returns:
        The ordinal suffix string (e.g., "1st", "2nd", "3rd", "24th")
    """
    if 11 <= day <= 13:
        return f'{day}th'

    suffixes = {1: 'st', 2: 'nd', 3: 'rd'}
    last_digit = day % 10
    suffix = suffixes.get(last_digit, 'th')
    return f'{day}{suffix}'


def calculate_progress(
    current_percentage: float,
    current_date: datetime | None = None,
    target_day: int = 1,
) -> ProgressResult:
    """
    Calculate if you're using credits faster or slower than expected.

    Args:
        current_percentage: Your current credit usage percentage (e.g., 25 for 25%)
        current_date: The date to calculate from (defaults to today)
        target_day: The renewal day of the month (defaults to 1)

    Returns:
        Dictionary with progress metrics including:
        - current_percentage: Input percentage
        - current_day: Current day of month
        - target_day: Renewal day
        - days_in_month: Days in current month
        - days_since_renewal: Days elapsed in billing cycle
        - days_in_billing_cycle: Total days in billing cycle
        - time_progress: Percentage of time elapsed
        - expected_percentage: Expected usage at this point
        - ratio: Usage ratio (>1 = too fast, <1 = conserving)
        - difference_percentage: Difference from expected
        - projected_usage: Projected total usage at renewal
        - projected_remaining: Projected remaining credits
        - status: "using too fast", "conserving well", or "on track"
    """
    if current_date is None:
        current_date = datetime.now()

    # Convert percentage to decimal
    current_pct = current_percentage / 100

    # Get the day of the month (1-31)
    current_day = current_date.day

    # Calculate which billing cycle we're in
    # If current day >= target_day, we're past renewal for this month
    # Otherwise, we're still in the cycle from last month's target_day
    if current_day >= target_day:
        # We're in the period from target_day of this month to target_day of next month
        days_since_renewal = current_day - target_day
        # Calculate when next renewal is
        if current_date.month == 12:
            next_renewal = current_date.replace(year=current_date.year + 1, month=1, day=target_day)
        else:
            next_renewal = current_date.replace(month=current_date.month + 1, day=target_day)
    else:
        # We're in the period from target_day of last month to target_day of this month
        days_since_renewal = current_day + (31 - target_day)  # Approximate, will recalculate properly
        # Calculate last renewal date
        if current_date.month == 1:
            last_renewal = current_date.replace(year=current_date.year - 1, month=12, day=target_day)
        else:
            last_renewal = current_date.replace(month=current_date.month - 1, day=target_day)
        # Calculate next renewal
        next_renewal = current_date.replace(day=target_day)
        # Proper days since renewal
        days_since_renewal = (current_date - last_renewal).days

    # Calculate total days in this billing cycle
    if current_day >= target_day:
        if current_date.month == 1:
            last_renewal = current_date.replace(year=current_date.year - 1, month=12, day=target_day)
        else:
            last_renewal = current_date.replace(month=current_date.month, day=target_day)
    else:
        if current_date.month == 1:
            last_renewal = current_date.replace(year=current_date.year - 1, month=12, day=target_day)
        else:
            last_renewal = current_date.replace(month=current_date.month - 1, day=target_day)

    days_in_billing_cycle = (next_renewal - last_renewal).days

    # Days in the current month (for display purposes)
    if current_date.month == 12:
        next_month = current_date.replace(year=current_date.year + 1, month=1, day=1)
    else:
        next_month = current_date.replace(month=current_date.month + 1, day=1)
    days_in_month = (next_month - timedelta(days=1)).day

    # Calculate time progress (how far through the billing cycle)
    time_progress = days_since_renewal / days_in_billing_cycle

    # Calculate the ratio: actual percentage vs expected percentage
    # Ratio > 1 means using credits faster than time (bad)
    # Ratio < 1 means using credits slower than time (good)
    ratio = current_pct / time_progress if time_progress > 0 else 0

    # Calculate how ahead or behind you are
    expected_pct = time_progress
    difference = current_pct - expected_pct
    difference_pct = difference * 100

    # Project usage at renewal date based on current rate
    # If we're 16 days into a 31-day cycle with 25% used, rate is 25/16 = 1.56% per day
    # At day 31: 1.56 * 31 = 48.4% projected usage
    #
    # If days_since_renewal=0 (i.e., we're on the renewal day), we can't calculate a rate yet. Therefore, we assume
    # the day is almost over and thus approximate the rate by setting the days_since_renewal=1.
    daily_rate = current_percentage / max(days_since_renewal, 1)
    projected_usage = daily_rate * days_in_billing_cycle
    projected_remaining = 100 - projected_usage

    # Status is inverted: using fewer credits than time = good (conserving)
    return {
        'current_percentage': current_percentage,
        'current_day': current_day,
        'target_day': target_day,
        'days_in_month': days_in_month,
        'days_since_renewal': days_since_renewal,
        'days_in_billing_cycle': days_in_billing_cycle,
        'time_progress': time_progress * 100,
        'expected_percentage': expected_pct * 100,
        'ratio': ratio,
        'difference_percentage': difference_pct,
        'projected_usage': projected_usage,
        'projected_remaining': projected_remaining,
        'status': 'using too fast' if difference > 0 else 'conserving well' if difference < 0 else 'on track',
    }
