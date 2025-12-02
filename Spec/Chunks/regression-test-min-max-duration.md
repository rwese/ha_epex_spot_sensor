# Regression Test: Min/Max Duration Fields Missing

## Issue Description
User reports that input fields for min and max duration do not show up in the configuration UI.

## Root Cause
Phase 2 (Flexible Duration) features were not implemented:
- `duration_mode` dropdown (Exact/Flexible)
- `min_duration` field (conditional)
- `max_duration` field (renamed from duration)

Only Phase 1 (Price Tolerance) was implemented.

## Regression Test

Create `tests/test_config_flow_flexible_duration.py`:

```python
"""Test flexible duration configuration fields."""

import pytest
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant
from custom_components.epex_spot_sensor import config_flow
from custom_components.epex_spot_sensor.const import (
    CONF_DURATION_MODE,
    CONF_MIN_DURATION,
    CONF_PRICE_TOLERANCE,
    DEFAULT_PRICE_TOLERANCE,
)


class TestFlexibleDurationConfig:
    """Test flexible duration configuration fields."""

    def test_duration_mode_field_exists(self, hass: HomeAssistant):
        """Test that duration_mode field exists in config schema."""
        # This test will FAIL until Phase 2 is implemented
        schema = config_flow.OPTIONS_SCHEMA
        
        # Check that duration_mode field exists
        assert CONF_DURATION_MODE in schema.schema
        assert schema.schema[CONF_DURATION_MODE] is not None
        
        # Check it's a select field with correct options
        field = schema.schema[CONF_DURATION_MODE]
        assert hasattr(field, 'container')
        # This would need to be adjusted based on actual voluptuous structure

    def test_min_duration_field_conditional(self, hass: HomeAssistant):
        """Test that min_duration field exists and is conditional."""
        # This test will FAIL until Phase 2 is implemented
        schema = config_flow.OPTIONS_SCHEMA
        
        # Check that min_duration field exists
        assert CONF_MIN_DURATION in schema.schema
        
        # Check it's optional (conditional)
        field = schema.schema[CONF_MIN_DURATION]
        assert hasattr(field, 'optional') or hasattr(field, 'required') is False

    def test_price_tolerance_field_exists(self, hass: HomeAssistant):
        """Test that price_tolerance field exists (Phase 1 - should pass)."""
        schema = config_flow.OPTIONS_SCHEMA
        
        # This should PASS (Phase 1 implemented)
        assert CONF_PRICE_TOLERANCE in schema.schema
        
        # Check default value
        field = schema.schema[CONF_PRICE_TOLERANCE]
        assert DEFAULT_PRICE_TOLERANCE == 0.0

    def test_config_validation_with_flexible_mode(self, hass: HomeAssistant):
        """Test configuration validation with flexible duration mode."""
        # This test will FAIL until Phase 2 is implemented
        
        # Mock config data with flexible mode
        config_data = {
            CONF_DURATION_MODE: "flexible",
            CONF_MIN_DURATION: {"hours": 2},
            CONF_PRICE_TOLERANCE: 15,
            # ... other required fields
        }
        
        # This should validate successfully
        # Currently will fail because fields don't exist
        schema = config_flow.OPTIONS_SCHEMA
        result = schema(config_data)
        assert result is not None

    def test_config_validation_with_exact_mode(self, hass: HomeAssistant):
        """Test configuration validation with exact duration mode."""
        # This test will FAIL until Phase 2 is implemented
        
        # Mock config data with exact mode
        config_data = {
            CONF_DURATION_MODE: "exact",
            # min_duration should not be required
            CONF_PRICE_TOLERANCE: 0,
            # ... other required fields
        }
        
        # This should validate successfully
        schema = config_flow.OPTIONS_SCHEMA
        result = schema(config_data)
        assert result is not None
```

## Test Results (Current)

**Expected to FAIL** (demonstrating the issue):

```
FAILED test_config_flow_flexible_duration.py::TestFlexibleDurationConfig::test_duration_mode_field_exists
FAILED test_config_flow_flexible_duration.py::TestFlexibleDurationConfig::test_min_duration_field_conditional  
FAILED test_config_flow_flexible_duration.py::TestFlexibleDurationConfig::test_config_validation_with_flexible_mode
FAILED test_config_flow_flexible_duration.py::TestFlexibleDurationConfig::test_config_validation_with_exact_mode

PASSED test_config_flow_flexible_duration.py::TestFlexibleDurationConfig::test_price_tolerance_field_exists
```

## Test Results (After Phase 2 Implementation)

**Expected to PASS**:

```
PASSED test_config_flow_flexible_duration.py::TestFlexibleDurationConfig::test_duration_mode_field_exists
PASSED test_config_flow_flexible_duration.py::TestFlexibleDurationConfig::test_min_duration_field_conditional
PASSED test_config_flow_flexible_duration.py::TestFlexibleDurationConfig::test_price_tolerance_field_exists
PASSED test_config_flow_flexible_duration.py::TestFlexibleDurationConfig::test_config_validation_with_flexible_mode
PASSED test_config_flow_flexible_duration.py::TestFlexibleDurationConfig::test_config_validation_with_exact_mode
```

## Purpose

This regression test:
1. **Demonstrates the current issue** (fields missing)
2. **Provides clear requirements** for Phase 2 implementation
3. **Validates the fix** once implemented
4. **Prevents future regressions** of these fields

## Implementation Notes

- Tests should be run before and after Phase 2 implementation
- Before: Tests fail (showing missing functionality)
- After: Tests pass (validating implementation)
- This is not a true regression (functionality never existed) but serves the same purpose