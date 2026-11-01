"""Tests for core calculation functions."""

from datetime import datetime

from aiusage.core import calculate_progress, ordinal_suffix

def test_ordinal_suffix():
    """Test ordinal suffix generation."""
    assert ordinal_suffix(1) == '1st'
    assert ordinal_suffix(2) == '2nd'
    assert ordinal_suffix(3) == '3rd'
    assert ordinal_suffix(4) == '4th'
    assert ordinal_suffix(11) == '11th'
    assert ordinal_suffix(12) == '12th'
    assert ordinal_suffix(13) == '13th'
    assert ordinal_suffix(21) == '21st'
    assert ordinal_suffix(22) == '22nd'
    assert ordinal_suffix(23) == '23rd'
    assert ordinal_suffix(24) == '24th'


def test_calculate_progress_basic():
    """Test basic progress calculation."""
    # Test with a known date: October 12, 2025, renewal day 24th
    test_date = datetime(2025, 10, 12)
    result = calculate_progress(25.0, current_date=test_date, target_day=24)

    assert result['current_percentage'] == 25.0
    assert result['target_day'] == 24
    assert result['current_day'] == 12
    assert result['days_since_renewal'] == 18  # Oct 12 - Sep 24 = 18 days
    assert result['days_in_billing_cycle'] == 30  # Sep 24 to Oct 24


def test_calculate_progress_basic2():
    """Test basic progress calculation."""
    # Test with a known date: October 12, 2025, renewal day 1st
    test_date = datetime(2025, 10, 12)
    result = calculate_progress(25.0, current_date=test_date, target_day=1)

    atol = 1e-3

    assert result['current_percentage'] == 25.0
    assert result['target_day'] == 1
    assert result['current_day'] == 12
    assert result['days_since_renewal'] == 11  # Oct 12 - Oct 1 = 11 days
    assert result['days_in_billing_cycle'] == 31  # Oct 1 to Oct 31
    assert abs(result['projected_usage'] - 25.0 * (31 / 11)) < atol  # 25% used in 11 days of 31 days


def test_calculate_progress_basic3():
    """Test basic progress calculation."""
    # Test with a known date: October 12, 2025, renewal day 12th
    test_date = datetime(2025, 10, 12)
    result = calculate_progress(25.0, current_date=test_date, target_day=12)

    atol = 1e-3

    assert result['current_percentage'] == 25.0
    assert result['target_day'] == 12
    assert result['current_day'] == 12
    assert result['days_since_renewal'] == 0  # Oct 12 - Oct 12 = 0 days
    assert result['days_in_billing_cycle'] == 31  # Oct 12 to Nov 12
    assert abs(result['projected_usage'] - 25.0 * (31 / 1)) < atol  # 25% used in 0 days of 31 days


def test_calculate_progress_conserving():
    """Test when conserving credits (using slower than time)."""
    test_date = datetime(2025, 10, 12)
    result = calculate_progress(25.0, current_date=test_date, target_day=24)

    assert result['ratio'] < 1.0
    assert result['status'] == 'conserving well'
    assert result['difference_percentage'] < 0
    assert result['projected_remaining'] > 0


def test_calculate_progress_using_fast():
    """Test when using credits too fast."""
    test_date = datetime(2025, 10, 12)
    result = calculate_progress(75.0, current_date=test_date, target_day=24)

    assert result['ratio'] > 1.0
    assert result['status'] == 'using too fast'
    assert result['difference_percentage'] > 0
    assert result['projected_usage'] > 100


def test_calculate_progress_default_date():
    """Test that it works with default (current) date."""
    result = calculate_progress(50.0, target_day=24)

    assert result is not None
    assert 'status' in result
    assert 'projected_usage' in result
