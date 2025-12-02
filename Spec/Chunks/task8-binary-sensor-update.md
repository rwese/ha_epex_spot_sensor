# Task 8: Update Binary Sensor for Flexible Duration

## Objective
Update `binary_sensor.py` to support flexible duration parameters and pass them to interval calculation functions.

## Files to Modify

### 1. `custom_components/epex_spot_sensor/binary_sensor.py`

#### Step 1: Add imports
```python
from .const import (
    # ... existing imports ...
    CONF_DURATION_MODE,
    CONF_MIN_DURATION,
    DurationModes,
)
```

#### Step 2: Update BinarySensor.__init__
Add new parameters:
```python
def __init__(
    self,
    hass: HomeAssistant,
    unique_id: str,
    name: str,
    entity_id: str,
    earliest_start_time: time,
    latest_end_time: time,
    duration: timedelta,  # This becomes max_duration
    duration_entity_id: str | None,
    interval_mode: str,
    price_mode: str,
    duration_mode: str,  # NEW
    min_duration: timedelta | None,  # NEW
    price_tolerance: float,  # Already added in Phase 1
    device_info: DeviceInfo | None = None,
) -> None:
```

Store the new parameters:
```python
self._duration_mode = duration_mode
self._min_duration = min_duration
```

#### Step 3: Update async_setup_entry
Pass new parameters from config:
```python
price_tolerance=config_entry.options.get(
    CONF_PRICE_TOLERANCE, DEFAULT_PRICE_TOLERANCE
),
duration_mode=config_entry.options.get(
    CONF_DURATION_MODE, DurationModes.EXACT
),
min_duration=config_entry.options.get(CONF_MIN_DURATION),
```

#### Step 4: Update interval calculation calls

**Contiguous mode (_update_state_for_contiguous):**
```python
result = calc_interval_for_contiguous(
    marketdata,
    earliest_start=earliest_start,
    latest_end=latest_end,
    duration=self._duration,  # max_duration
    most_expensive=self._price_mode == PriceModes.MOST_EXPENSIVE.value,
    price_tolerance_percent=self._price_tolerance,
    min_duration=self._min_duration if self._duration_mode == DurationModes.FLEXIBLE.value else None,
)
```

**Intermittent mode (_update_state_for_intermittent):**
```python
intervals = calc_intervals_for_intermittent(
    marketdata=marketdata,
    earliest_start=earliest_start,
    latest_end=latest_end,
    duration=self._duration,  # max_duration
    most_expensive=self._price_mode == PriceModes.MOST_EXPENSIVE.value,
    price_tolerance_percent=self._price_tolerance,
    min_duration=self._min_duration if self._duration_mode == DurationModes.FLEXIBLE.value else None,
)
```

#### Step 5: Handle duration entity override
When duration_entity_id is set, override flexible mode (Decision 5):
```python
def _calculate_duration(self):
    self._duration = self._default_duration
    self._min_duration = None  # Reset flexible settings
    
    if self._duration_entity_id is None:
        return
    
    # ... existing entity logic ...
    
    # When entity is active, force exact mode
    self._duration_mode = DurationModes.EXACT.value
    self._min_duration = None
```

## Requirements

- MUST pass min_duration only when duration_mode is FLEXIBLE
- MUST pass None for min_duration in exact mode (backward compatibility)
- MUST handle duration entity override correctly
- MUST maintain all existing functionality

## Testing

After implementation:
1. Binary sensor accepts new parameters
2. Passes correct parameters to interval functions
3. Duration entity overrides flexible mode
4. All existing tests still pass

## Reference

- See: `Spec/Backlog/DECISIONS-flexible-duration-with-price-tolerance.md` - Decision 5
- Current code: `custom_components/epex_spot_sensor/binary_sensor.py`
