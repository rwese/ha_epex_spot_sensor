# Task 2: Implement Price Tolerance in Contiguous Mode

## Objective

Modify `contiguous_interval.py` to support price tolerance parameter.

## Algorithm Overview

Current behavior:

1. Generate candidate start times
2. Calculate price for each interval
3. Find the single cheapest/most expensive interval

New behavior with tolerance:

1. Generate candidate start times
2. Calculate price for each interval
3. Find the optimal (cheapest/most expensive) interval
4. If tolerance > 0:
   - Calculate price threshold based on optimal price
   - Filter all intervals within threshold
   - Among filtered intervals, prefer earliest start time
5. Return selected interval

## Implementation Details

### Step 1: Add tolerance parameter

Modify function signature:

```python
def calc_interval_for_contiguous(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    duration: timedelta,
    most_expensive: bool = False,
    price_tolerance_percent: float = 0.0,  # NEW PARAMETER
):
```

### Step 2: Modify `_find_extreme_price_interval`

Add tolerance parameter and logic:

```python
def _find_extreme_price_interval(
    marketdata,
    start_times,
    duration: timedelta,
    most_expensive: bool = False,
    price_tolerance_percent: float = 0.0,  # NEW PARAMETER
):
    # Existing code to find optimal interval
    interval_price: float | None = None
    interval_start_time: datetime | None = None

    # ... existing loop to find optimal ...

    if interval_start_time is None:
        return None

    optimal_result = {
        "start": interval_start_time,
        "end": interval_start_time + duration,
        "interval_price": interval_price,
        "price_per_hour": interval_price * SECONDS_PER_HOUR / duration.total_seconds(),
    }

    # NEW: If tolerance is 0, return optimal (backward compatibility)
    if price_tolerance_percent == 0.0:
        return optimal_result

    # NEW: Calculate price threshold
    price_per_hour = optimal_result["price_per_hour"]
    if most_expensive:
        # For most expensive mode, threshold is lower bound
        threshold = price_per_hour * (1 - price_tolerance_percent / 100)
        def within_threshold(price):
            return price >= threshold
    else:
        # For cheapest mode, threshold is upper bound
        threshold = price_per_hour * (1 + price_tolerance_percent / 100)
        def within_threshold(price):
            return price <= threshold

    # NEW: Find all intervals within threshold
    candidates = []
    for start in start_times:
        price = _calc_interval_price(marketdata, start, duration)
        if price is None:
            continue

        price_per_hour_candidate = price * SECONDS_PER_HOUR / duration.total_seconds()

        if within_threshold(price_per_hour_candidate):
            candidates.append({
                "start": start,
                "end": start + duration,
                "interval_price": price,
                "price_per_hour": price_per_hour_candidate,
            })

    # NEW: If no candidates within threshold, fall back to optimal
    if len(candidates) == 0:
        _LOGGER.warning(
            "No intervals found within price tolerance (%.1f%%), "
            "using optimal interval",
            price_tolerance_percent
        )
        return optimal_result

    # NEW: Prefer earliest start time (Decision 3)
    candidates.sort(key=lambda x: x["start"])
    return candidates[0]
```

### Step 3: Update function call

In `calc_interval_for_contiguous`, pass tolerance to helper:

```python
return _find_extreme_price_interval(
    marketdata, start_times, duration, most_expensive, price_tolerance_percent
)
```

## Edge Cases to Handle

1. **Tolerance = 0%:** Must return exact same result as current behavior
2. **No intervals within threshold:** Fall back to optimal with warning log
3. **All intervals within threshold:** Select earliest start time
4. **Tolerance = 100%:** All intervals acceptable, select earliest

## Testing Requirements

Create `tests/test_price_tolerance_contiguous.py` with:

- Test tolerance=0 matches current behavior
- Test tolerance=10%, 20%, 50%
- Test "prefer earlier" when multiple options
- Test fallback when no intervals within threshold
- Test tolerance=100% (all acceptable)

## Reference

- See: `Spec/Backlog/DECISIONS-flexible-duration-with-price-tolerance.md` - Decisions 2, 3, 7
- Current code: `custom_components/epex_spot_sensor/contiguous_interval.py`
