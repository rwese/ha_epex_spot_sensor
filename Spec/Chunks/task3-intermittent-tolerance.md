# Task 3: Implement Price Tolerance in Intermittent Mode

## Objective

Modify `intermittent_interval.py` to support price tolerance parameter.

## Algorithm Overview

Current behavior:

1. Filter market data to time window
2. Sort by price (ascending for cheapest, descending for most expensive)
3. Greedily select slots in strict price order until duration met

New behavior with tolerance:

1. Filter market data to time window
2. Sort by price
3. Find reference price (cheapest/most expensive slot)
4. If tolerance > 0:
   - Calculate price threshold
   - Filter slots within threshold
   - Sort filtered slots by start time (prefer earlier)
   - Select slots until duration met
5. If insufficient slots within threshold:
   - Fall back to strict price ordering
6. Return selected intervals

## Implementation Details

### Step 1: Add tolerance parameter

Modify function signature:

```python
def calc_intervals_for_intermittent(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    duration: timedelta,
    most_expensive: bool = False,
    price_tolerance_percent: float = 0.0,  # NEW PARAMETER
):
```

### Step 2: Implement tolerance logic

After filtering and sorting market data:

```python
def calc_intervals_for_intermittent(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    duration: timedelta,
    most_expensive: bool = False,
    price_tolerance_percent: float = 0.0,
):
    """Calculate price for given start time and duration."""
    if len(marketdata) == 0:
        return None

    if marketdata[-1].end_time < latest_end:
        return None

    # filter intervals which fit to start- and end-time (including overlapping)
    marketdata = [
        e
        for e in marketdata
        if earliest_start < e.end_time and latest_end > e.start_time
    ]

    # sort by price
    marketdata.sort(key=lambda e: e.price, reverse=most_expensive)

    # NEW: If tolerance > 0, filter by price threshold
    if price_tolerance_percent > 0.0:
        # Reference price is the first element (cheapest or most expensive)
        reference_price = marketdata[0].price

        # Calculate threshold
        if most_expensive:
            threshold = reference_price * (1 - price_tolerance_percent / 100)
            acceptable_slots = [e for e in marketdata if e.price >= threshold]
        else:
            threshold = reference_price * (1 + price_tolerance_percent / 100)
            acceptable_slots = [e for e in marketdata if e.price <= threshold]

        # Sort acceptable slots by start time (prefer earlier)
        acceptable_slots.sort(key=lambda e: e.start_time)

        # Try to satisfy duration with acceptable slots
        test_intervals = _select_intervals_from_slots(
            acceptable_slots, earliest_start, latest_end, duration
        )

        # Check if we satisfied the duration
        total_duration = sum(
            (i.end_time - i.start_time).total_seconds()
            for i in test_intervals
        )

        if total_duration >= duration.total_seconds():
            # Success with tolerance
            return test_intervals
        else:
            # Fall back to strict ordering
            _LOGGER.warning(
                "Insufficient slots within price tolerance (%.1f%%), "
                "falling back to strict price ordering",
                price_tolerance_percent
            )
            # Continue with original marketdata (sorted by price)

    # Original algorithm (or fallback)
    return _select_intervals_from_slots(
        marketdata, earliest_start, latest_end, duration
    )


def _select_intervals_from_slots(slots, earliest_start, latest_end, duration):
    """Helper function to select intervals from given slots."""
    active_time: timedelta = timedelta(seconds=0)
    intervals = []

    for count, mp in enumerate(slots):
        interval_start_time = (
            earliest_start if mp.start_time < earliest_start else mp.start_time
        )
        interval_end_time = latest_end if mp.end_time > latest_end else mp.end_time

        active_duration_in_this_segment = interval_end_time - interval_start_time

        if active_time + active_duration_in_this_segment > duration:
            # we don't need the full active_duration_in_this_segment
            active_duration_in_this_segment = duration - active_time

            # check if we can connect to an existing interval
            connects_to_next = False
            for i in intervals:
                if i.start_time == interval_end_time:
                    connects_to_next = True
                    break

            connects_to_prev = False
            for i in intervals:
                if i.end_time == interval_start_time:
                    connects_to_prev = True
                    break

            if connects_to_next and not connects_to_prev:
                # align to end
                interval_start_time = interval_end_time - active_duration_in_this_segment
            else:
                # align to start
                interval_end_time = interval_start_time + active_duration_in_this_segment
        else:
            # take full segment
            pass

        price = (
            mp.price
            * active_duration_in_this_segment.total_seconds()
            / SECONDS_PER_HOUR
        )

        intervals.append(
            Interval(
                start_time=interval_start_time,
                end_time=interval_start_time + active_duration_in_this_segment,
                price=price,
                rank=count,
            )
        )

        active_time += active_duration_in_this_segment

        if active_time == duration:
            break

    return intervals
```

## Key Changes

1. **Extract selection logic** into `_select_intervals_from_slots()` helper function
2. **Add tolerance filtering** before selection
3. **Sort by start time** when using tolerance (prefer earlier)
4. **Fallback logic** if tolerance too restrictive
5. **Maintain backward compatibility** when tolerance=0

## Edge Cases to Handle

1. **Tolerance = 0%:** Use original algorithm (no filtering)
2. **Insufficient slots within threshold:** Fall back to strict price ordering with warning
3. **All slots within threshold:** Select earliest slots
4. **Partial slot needed:** Existing connectivity optimization still applies

## Testing Requirements

Create `tests/test_price_tolerance_intermittent.py` with:

- Test tolerance=0 matches current behavior
- Test tolerance=10%, 20%, 50%
- Test "prefer earlier" when multiple options
- Test fallback when insufficient slots
- Test tolerance=100% (all acceptable)
- Test partial slot handling with tolerance

## Reference

- See: `Spec/Backlog/DECISIONS-flexible-duration-with-price-tolerance.md` - Decisions 2, 3, 4, 7
- Current code: `custom_components/epex_spot_sensor/intermittent_interval.py`
