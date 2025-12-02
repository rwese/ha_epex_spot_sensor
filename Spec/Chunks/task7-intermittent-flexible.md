# Task 7: Implement Flexible Duration in Intermittent Mode

## Objective
Modify `intermittent_interval.py` to support flexible duration with min/max bounds and price threshold stopping.

## Algorithm Overview

Current behavior:
1. Sort slots by price
2. Greedily select until exact duration reached

New behavior with flexible duration:
1. Sort slots by price
2. Select slots until min_duration satisfied (strict price order)
3. Continue adding slots up to max_duration
4. Stop when: (a) max_duration reached, OR (b) next slot exceeds price threshold
5. Apply price tolerance filtering if configured

## Implementation Details

### Step 1: Add flexible duration parameters

Modify function signature:
```python
def calc_intervals_for_intermittent(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    duration: timedelta,  # This becomes max_duration
    most_expensive: bool = False,
    price_tolerance_percent: float = 0.0,
    min_duration: timedelta | None = None,  # NEW: minimum duration
):
    # If min_duration is None, use exact mode (backward compatibility)
    if min_duration is None:
        min_duration = duration  # exact mode
    
    # duration parameter now represents max_duration
    max_duration = duration
```

### Step 2: Implement flexible selection logic

Modify the main selection loop:

```python
def calc_intervals_for_intermittent_flexible(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    min_duration: timedelta,
    max_duration: timedelta,
    most_expensive: bool = False,
    price_tolerance_percent: float = 0.0,
):
    """Calculate intervals with flexible duration."""
    if len(marketdata) == 0:
        return None

    if marketdata[-1].end_time < latest_end:
        return None

    # Filter market data to time window
    marketdata = [
        e for e in marketdata
        if earliest_start < e.end_time and latest_end > e.start_time
    ]

    # Apply price tolerance filtering first
    if price_tolerance_percent > 0.0:
        reference_price = marketdata[0].price
        threshold = reference_price * (1 + price_tolerance_percent / 100) if not most_expensive else reference_price * (1 - price_tolerance_percent / 100)
        marketdata = [e for e in marketdata if e.price <= threshold if not most_expensive else e.price >= threshold]
        
        if len(marketdata) == 0:
            _LOGGER.warning("No slots within price tolerance (%.1f%%)", price_tolerance_percent)
            return None

    # Sort by price and start time preference
    marketdata.sort(key=lambda e: (e.price, e.start_time), reverse=most_expensive)

    # Select intervals with flexible duration
    active_time = timedelta(seconds=0)
    intervals = []
    reference_price_per_hour = None

    for count, mp in enumerate(marketdata):
        interval_start_time = max(earliest_start, mp.start_time)
        interval_end_time = min(latest_end, mp.end_time)
        active_duration_in_this_segment = interval_end_time - interval_start_time

        if active_time + active_duration_in_this_segment > max_duration:
            active_duration_in_this_segment = max_duration - active_time

        # Calculate price for this segment
        price = mp.price * active_duration_in_this_segment.total_seconds() / SECONDS_PER_HOUR
        price_per_hour = mp.price

        # Check price threshold for additional segments (after min_duration)
        if active_time >= min_duration and reference_price_per_hour is not None:
            # Calculate how much more expensive this slot is
            price_ratio = price_per_hour / reference_price_per_hour
            if price_ratio > (1 + price_tolerance_percent / 100):
                # Too expensive, stop here
                break

        intervals.append(Interval(
            start_time=interval_start_time,
            end_time=interval_start_time + active_duration_in_this_segment,
            price=price,
            rank=count,
        ))

        active_time += active_duration_in_this_segment

        # Set reference price after min_duration satisfied
        if active_time >= min_duration and reference_price_per_hour is None:
            reference_price_per_hour = price_per_hour

        if active_time >= max_duration:
            break

    # Ensure we meet minimum duration
    total_duration = sum((i.end_time - i.start_time).total_seconds() for i in intervals)
    if total_duration < min_duration.total_seconds():
        return None  # Cannot satisfy minimum

    return intervals
```

## Key Features

1. **Two-Phase Selection**:
   - Phase 1: Strict price order until min_duration satisfied
   - Phase 2: Price threshold stopping until max_duration reached

2. **Price Threshold Logic**:
   - After min_duration, check if next slot exceeds threshold
   - Threshold based on last slot's price + tolerance percentage
   - Stops adding expensive slots opportunistically

3. **Integration with Price Tolerance**:
   - Applies individual slot filtering first
   - Then applies price threshold stopping
   - Compatible with existing tolerance feature

## Requirements

- MUST satisfy min_duration (guaranteed minimum)
- MUST not exceed max_duration (hard limit)
- MUST stop at price threshold when beneficial
- MUST work with existing price tolerance feature
- MUST maintain backward compatibility

## Testing Requirements

Create `tests/test_intermittent_interval_flexible.py` with:
- Test exact mode (min = max)
- Test flexible range with price threshold stopping
- Test min_duration guarantee
- Test max_duration limit
- Test with price tolerance
- Test edge cases

## Reference

- See: `Spec/Backlog/DECISIONS-flexible-duration-with-price-tolerance.md` - Decisions 1, 2, 4
- Current code: `custom_components/epex_spot_sensor/intermittent_interval.py`
