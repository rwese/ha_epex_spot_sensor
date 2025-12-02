# Task 4: Add Duration Mode Configuration

## Objective
Add `duration_mode` configuration parameter to support Exact vs Flexible duration modes.

## Files to Modify

### 1. `custom_components/epex_spot_sensor/const.py`

Add new constants:
```python
CONF_DURATION_MODE = "duration_mode"
CONF_MIN_DURATION = "min_duration"

class DurationModes(Enum):
    """Duration modes for config validation."""
    
    EXACT = "exact"
    FLEXIBLE = "flexible"

DEFAULT_DURATION_MODE = DurationModes.EXACT
```

### 2. `custom_components/epex_spot_sensor/config_flow.py`

Add to OPTIONS_SCHEMA (before duration field):
```python
vol.Required(
    CONF_DURATION_MODE, default=DurationModes.EXACT
): selector.SelectSelector(
    selector.SelectSelectorConfig(
        translation_key=CONF_DURATION_MODE,
        mode=selector.SelectSelectorMode.LIST,
        options=[e.value for e in DurationModes],
    ),
),
```

Import the new constants and enum.

### 3. `custom_components/epex_spot_sensor/translations/en.json`

Add translations:
```json
{
  "config": {
    "step": {
      "user": {
        "data": {
          "duration_mode": "Duration Mode"
        },
        "data_description": {
          "duration_mode": "Select whether to use exact duration or flexible duration with minimum/maximum bounds."
        }
      }
    }
  },
  "options": {
    "step": {
      "init": {
        "data": {
          "duration_mode": "Duration Mode"
        },
        "data_description": {
          "duration_mode": "Select whether to use exact duration or flexible duration with minimum/maximum bounds."
        }
      }
    }
  }
}
```

## Requirements

- Default value must be `DurationModes.EXACT` (backward compatibility)
- Options: `["exact", "flexible"]`
- Must be a required field with default

## Testing

After implementation:
1. Configuration UI shows duration mode dropdown
2. Default value is "exact"
3. Can select "flexible" mode
4. Field is properly translated

## Reference

See: `Spec/Backlog/DECISIONS-flexible-duration-with-price-tolerance.md` - Decision 6
