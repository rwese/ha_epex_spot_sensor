# Task 1: Add Price Tolerance Configuration

## Objective
Add `price_tolerance` configuration parameter to the EPEX Spot Sensor configuration schema.

## Files to Modify

### 1. `custom_components/epex_spot_sensor/const.py`

Add new constant:
```python
CONF_PRICE_TOLERANCE = "price_tolerance"
DEFAULT_PRICE_TOLERANCE = 0.0
```

### 2. `custom_components/epex_spot_sensor/config_flow.py`

Add to `OPTIONS_SCHEMA` (after interval mode, before closing brace):
```python
vol.Optional(
    CONF_PRICE_TOLERANCE, default=DEFAULT_PRICE_TOLERANCE
): selector.NumberSelector(
    selector.NumberSelectorConfig(
        mode=selector.NumberSelectorMode.BOX,
        min=0,
        max=100,
        step=1,
        unit_of_measurement="%",
    ),
),
```

Import the new constant at the top:
```python
from .const import (
    # ... existing imports ...
    CONF_PRICE_TOLERANCE,
)
```

### 3. `custom_components/epex_spot_sensor/translations/en.json`

Add translation for the new field:
```json
{
  "config": {
    "step": {
      "user": {
        "data": {
          "price_tolerance": "Price Tolerance (%)"
        },
        "data_description": {
          "price_tolerance": "Allow time slots within ±X% of the cheapest/most expensive price. 0% = exact matching (default)."
        }
      }
    }
  },
  "options": {
    "step": {
      "init": {
        "data": {
          "price_tolerance": "Price Tolerance (%)"
        },
        "data_description": {
          "price_tolerance": "Allow time slots within ±X% of the cheapest/most expensive price. 0% = exact matching (default)."
        }
      }
    }
  }
}
```

## Requirements

- Default value must be 0.0 (backward compatibility)
- Range: 0-100%
- Step: 1
- Unit: percentage (%)
- Must be optional field

## Testing

After implementation, verify:
1. Configuration UI shows new field
2. Default value is 0%
3. Value can be changed and saved
4. Value is accessible in binary_sensor.py

## Reference

See: `Spec/Backlog/DECISIONS-flexible-duration-with-price-tolerance.md` - Decision 2
