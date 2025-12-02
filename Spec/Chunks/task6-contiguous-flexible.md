# Task 6: Implement Flexible Duration in Contiguous Mode

## Objective
Modify `contiguous_interval.py` to support flexible duration with min/max bounds.

## Algorithm Overview

Current behavior:
1. Find single interval of exact duration
2. Return the cheapest/most expensive option

New behavior with flexible duration:
1. Generate candidate intervals between min_duration and max_duration
2. Calculate price for each candidate interval
3. Find optimal interval within the range
4. Apply price tolerance if configured
5. Return selected interval

## Implementation Details

### Step 1: Add flexible duration parameters

Modify function signature:
```python
def calc_interval_for_contiguous(
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

### Step 2: Generate flexible candidate intervals

Instead of generating candidates for a single duration, generate for a range:

```python
def _calc_flexible_start_times(
    marketdata, earliest_start: datetime, latest_end: datetime, 
    min_duration: timedelta, max_duration: timedelta
):
    """Calculate meaningful start times for flexible duration range."""
    start_times = set()
    
    # Generate candidates for each duration in range
    # This is more complex - we need to find start times that work for ANY duration in range
    # For simplicity, we can:
    # 1. Generate candidates for min_duration
    # 2. Generate candidates for max_duration  
    # 3. Combine and deduplicate
    
    # Candidates for min_duration
    min_candidates = _calc_start_times(marketdata, earliest_start, latest_end, min_duration)
    
    # Candidates for max_duration
    max_candidates = _calc_start_times(marketdata, earliest_start, latest_end, max_duration)
    
    # Combine
    start_times.update(min_candidates)
    start_times.update(max_candidates)
    
    return sorted(list(set(start_times)))
```

### Step 3: Evaluate intervals across duration range

Modify `_find_extreme_price_interval` to evaluate multiple durations:

```python
def _find_flexible_extreme_price_interval(
    marketdata, start_times, min_duration: timedelta, max_duration: timedelta,
    most_expensive: bool = False, price_tolerance_percent: float = 0.0
):
    """Find best interval within flexible duration range."""
    
    best_result = None
    best_price_per_hour = None
    
    # For each candidate start time
    for start in start_times:
        # Try different durations from min to max
        # For efficiency, try a few key durations: min, max, and maybe midpoint
        
        test_durations = [
            min_duration,
            max_duration,
        ]
        
        # Add midpoint if significantly different
        if max_duration > min_duration * 2:
            midpoint = min_duration + (max_duration - min_duration) / 2
            test_durations.append(midpoint)
        
        for test_duration in test_durations:
            if start + test_duration > latest_end:
                continue
                
            price = _calc_interval_price(marketdata, start, test_duration)
            if price is None:
                continue
            
            price_per_hour = price * SECONDS_PER_HOUR / test_duration.total_seconds()
            
            # Check if this is better than current best
            is_better = (
                best_price_per_hour is None or
                (price_per_hour < best_price_per_hour if not most_expensive 
                 else price_per_hour > best_price_per_hour)
            )
            
            if is_better:
                best_result = {
                    "start": start,
                    "end": start + test_duration,
                    "interval_price": price,
                    "price_per_hour": price_per_hour,
                }
                best_price_per_hour = price_per_hour
    
    # Apply price tolerance logic (reuse existing logic)
    if best_result and price_tolerance_percent > 0.0:
        # Find all intervals within tolerance of best_result
        # Return earliest among acceptable options
        pass  # Reuse existing tolerance logic
    
    return best_result
```

## Key Challenges

1. **Performance**: Evaluating multiple durations per start time
2. **Optimization**: Finding good candidates without exhaustive search
3. **Integration**: Combining with existing price tolerance logic

## Requirements

- MUST support min_duration to max_duration range
- MUST work with existing price tolerance feature
- MUST maintain backward compatibility (min_duration=None)
- MUST prefer cost optimization within duration flexibility

## Testing Requirements

Create `tests/test_contiguous_interval_flexible.py` with:
- Test exact mode (min_duration = max_duration)
- Test flexible range (min < max)
- Test with price tolerance
- Test edge cases (no valid intervals in range)

## Reference

- See: `Spec/Backlog/DECISIONS-flexible-duration-with-price-tolerance.md` - Decision 1
- Current code: `custom_components/epex_spot_sensor/contiguous_interval.py`
