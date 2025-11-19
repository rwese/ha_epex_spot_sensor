from datetime import datetime, timedelta
import pytest
from custom_components.epex_spot_sensor.intermittent_interval import (
    calc_intervals_for_intermittent,
)

class MockMarketPrice:
    def __init__(self, start_time, end_time, price):
        self.start_time = start_time
        self.end_time = end_time
        self.price = price

def test_calc_intervals_for_intermittent_simple():
    start = datetime(2023, 10, 1, 0, 0, 0)
    marketdata = [
        MockMarketPrice(start + timedelta(hours=i), start + timedelta(hours=i+1), price)
        for i, price in enumerate([10, 5, 20, 10])
    ]
    
    # Duration 2 hours, find cheapest (5 and 10)
    intervals = calc_intervals_for_intermittent(
        marketdata,
        earliest_start=start,
        latest_end=start + timedelta(hours=4),
        duration=timedelta(hours=2),
        most_expensive=False
    )
    
    assert intervals is not None
    assert len(intervals) == 2
    
    # Sorted by start time in output? No, the function returns them in order of processing or price?
    # The function sorts by price internally to pick, but returns a list.
    # Let's check the values.
    prices = sorted([i.price for i in intervals])
    assert prices == [5.0, 10.0]
    
    # Check total active time
    total_time = sum([ (i.end_time - i.start_time).total_seconds() for i in intervals ])
    assert total_time == 7200 # 2 hours

def test_calc_intervals_for_intermittent_most_expensive():
    start = datetime(2023, 10, 1, 0, 0, 0)
    marketdata = [
        MockMarketPrice(start + timedelta(hours=i), start + timedelta(hours=i+1), price)
        for i, price in enumerate([10, 5, 20, 10])
    ]
    
    # Duration 1 hour, find most expensive (20)
    intervals = calc_intervals_for_intermittent(
        marketdata,
        earliest_start=start,
        latest_end=start + timedelta(hours=4),
        duration=timedelta(hours=1),
        most_expensive=True
    )
    
    assert intervals is not None
    assert len(intervals) == 1
    assert intervals[0].price == 20.0

def test_calc_intervals_for_intermittent_partial_slots():
    start = datetime(2023, 10, 1, 0, 0, 0)
    marketdata = [
        MockMarketPrice(start + timedelta(hours=i), start + timedelta(hours=i+1), price)
        for i, price in enumerate([10, 5, 20, 10])
    ]
    
    # Duration 1.5 hours. Cheapest is 1h at 5, and 0.5h at 10 (either first or last slot)
    # The logic sorts by price. 
    # 1. 5.0 (01:00-02:00)
    # 2. 10.0 (00:00-01:00) OR 10.0 (03:00-04:00). Stable sort?
    # Let's see.
    
    intervals = calc_intervals_for_intermittent(
        marketdata,
        earliest_start=start,
        latest_end=start + timedelta(hours=4),
        duration=timedelta(hours=1.5),
        most_expensive=False
    )
    
    assert intervals is not None
    # Should have 2 intervals
    assert len(intervals) == 2
    
    # Calculate total price
    # 1 hour * 5 = 5
    # 0.5 hour * 10 = 5
    # Total price attribute on interval object is price * duration / hour
    # Interval 1: price=5, duration=1h -> val=5
    # Interval 2: price=10, duration=0.5h -> val=5
    
    total_val = sum([i.price for i in intervals])
    assert total_val == 10.0

def test_calc_intervals_for_intermittent_insufficient_data():
    start = datetime(2023, 10, 1, 0, 0, 0)
    marketdata = [
        MockMarketPrice(start + timedelta(hours=i), start + timedelta(hours=i+1), 10)
        for i in range(2)
    ]
    
    intervals = calc_intervals_for_intermittent(
        marketdata,
        earliest_start=start,
        latest_end=start + timedelta(hours=4),
        duration=timedelta(hours=1),
        most_expensive=False
    )
    
    assert intervals is None
