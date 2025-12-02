# Task 5: Add Min Duration Configuration

## Objective
Add `min_duration` configuration parameter that appears conditionally when duration_mode is "flexible".

## Files to Modify

### 1. `custom_components/epex_spot_sensor/config_flow.py`

Add after duration_mode field:
```python
vol.Optional(CONF_MIN_DURATION): selector.DurationSelector(),
```

Import CONF_MIN_DURATION from const.py.

### 2. `custom_components/epex_spot_sensor/translations/en.json`

Add translations:
```json
{
  "config": {
    "step": {
      "user": {
        "data": {
          "min_duration": "Minimum Duration"
        },
        "data_description": {
          "min_duration": "Minimum duration to run when using flexible mode. Must be less than maximum duration."
        }
      }
    }
  },
  "options": {
    "step": {
      "init": {
        "data": {
          "min_duration": "Minimum Duration"
        },
        "data_description": {
          "min_duration": "Minimum duration to run when using flexible mode. Must be less than maximum duration."
        }
      }
    }
  }
}
```

## Conditional Display Logic

The min_duration field should only appear when duration_mode is set to "flexible". This requires implementing conditional field display in the config flow.

However, Home Assistant's config flow doesn't natively support conditional fields in the schema. We need to implement this using a custom approach:

### Option A: Dynamic Schema (Recommended)
Modify the config flow to return different schemas based on current values:

```python
def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
    """Return config entry title."""
    return options.get(CONF_NAME, "EPEX Spot Sensor")

def async_get_options_flow(self, config_entry):
    """Return options flow for this handler."""
    return OptionsFlowHandler(config_entry)

class OptionsFlowHandler(SchemaConfigFlowHandler, domain=DOMAIN):
    """Handle options flow with conditional fields."""

    def async_get_options_flow_config_schema(self, options: dict[str, Any]) -> vol.Schema:
        """Return schema with conditional fields."""
        duration_mode = options.get(CONF_DURATION_MODE, DurationModes.EXACT)
        
        base_schema = vol.Schema({
            vol.Required(CONF_DURATION_MODE, default=duration_mode): selector.SelectSelector(...),
            # ... other fields ...
        })
        
        if duration_mode == DurationModes.FLEXIBLE.value:
            base_schema = base_schema.extend({
                vol.Optional(CONF_MIN_DURATION): selector.DurationSelector(),
            })
        
        return base_schema
```

### Option B: Always Show, Validate Conditionally
Show the field always but validate it's only set when duration_mode is flexible.

## Requirements

- Field is optional (not required)
- Only appears when duration_mode = "flexible"
- Type: Duration selector (hours, minutes, seconds)
- Must be less than maximum duration (validation needed)
- Clear user guidance in description

## Testing

After implementation:
1. Field appears only when duration_mode = "flexible"
2. Field is hidden when duration_mode = "exact"
3. Can set duration values (hours, minutes, seconds)
4. Field is properly translated

## Reference

See: `Spec/Backlog/DECISIONS-flexible-duration-with-price-tolerance.md` - Decision 6
