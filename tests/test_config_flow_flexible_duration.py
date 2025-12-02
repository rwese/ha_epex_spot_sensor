"""Test flexible duration configuration fields."""

import pytest
import voluptuous as vol
from custom_components.epex_spot_sensor import config_flow
from custom_components.epex_spot_sensor.const import (
    CONF_DURATION_MODE,
    CONF_MIN_DURATION,
    CONF_PRICE_TOLERANCE,
)


class TestFlexibleDurationConfig:
    """Test flexible duration configuration fields."""

    def test_duration_mode_field_exists(self):
        """Test that duration_mode field exists in options schema."""
        # Test with exact mode
        schema = config_flow.OptionsFlowHandler.async_get_options_flow_config_schema({})

        # Check that duration_mode field exists
        schema_dict = schema.validators[0].schema
        assert CONF_DURATION_MODE in schema_dict

    def test_min_duration_field_exists_when_flexible(self):
        """Test that min_duration field exists when duration_mode is flexible."""
        # Test with flexible mode
        schema = config_flow.OptionsFlowHandler.async_get_options_flow_config_schema(
            {CONF_DURATION_MODE: "flexible"}
        )

        # Check that min_duration field exists
        schema_dict = schema.validators[0].schema
        assert CONF_MIN_DURATION in schema_dict

    def test_min_duration_field_not_exists_when_exact(self):
        """Test that min_duration field does not exist when duration_mode is exact."""
        # Test with exact mode
        schema = config_flow.OptionsFlowHandler.async_get_options_flow_config_schema(
            {CONF_DURATION_MODE: "exact"}
        )

        # Check that min_duration field does not exist
        schema_dict = schema.validators[0].schema
        assert CONF_MIN_DURATION not in schema_dict

    def test_price_tolerance_field_exists(self):
        """Test that price_tolerance field exists (Phase 1 - should pass)."""
        schema = config_flow.OPTIONS_SCHEMA

        # This should PASS (Phase 1 implemented)
        assert CONF_PRICE_TOLERANCE in schema.schema

    def test_config_validation_with_exact_mode(self):
        """Test that config validation works with exact mode."""
        schema = config_flow.OptionsFlowHandler.async_get_options_flow_config_schema({})

        # Try to create config with exact mode
        config_data = {
            "earliest_start_time": "22:00:00",
            "latest_end_time": "06:00:00",
            "duration_mode": "exact",
            "duration": {"hours": 4},
            "price_mode": "cheapest",
            "interval_mode": "intermittent",
            "price_tolerance": 15,
        }

        # This should work
        result = schema(config_data)
        assert result is not None

    def test_config_validation_with_flexible_mode(self):
        """Test config validation with flexible mode including min_duration."""
        schema = config_flow.OptionsFlowHandler.async_get_options_flow_config_schema(
            {CONF_DURATION_MODE: "flexible"}
        )

        # Try to create config with flexible mode
        config_data = {
            "earliest_start_time": "22:00:00",
            "latest_end_time": "06:00:00",
            "duration_mode": "flexible",
            "duration": {"hours": 4},
            "min_duration": {"hours": 2},
            "price_mode": "cheapest",
            "interval_mode": "intermittent",
            "price_tolerance": 15,
        }

        # This should work
        result = schema(config_data)
        assert result is not None

    def test_min_duration_validation_greater_than_duration(self):
        """Test that min_duration > duration raises Invalid."""
        schema = config_flow.OptionsFlowHandler.async_get_options_flow_config_schema(
            {CONF_DURATION_MODE: "flexible"}
        )

        config_data = {
            "earliest_start_time": "22:00:00",
            "latest_end_time": "06:00:00",
            "duration_mode": "flexible",
            "duration": {"hours": 2},
            "min_duration": {"hours": 3},  # min > duration
            "price_mode": "cheapest",
            "interval_mode": "intermittent",
            "price_tolerance": 15,
        }

        with pytest.raises(
            vol.Invalid, match="min_duration must be less than or equal to duration"
        ):
            schema(config_data)

    def test_min_duration_validation_less_or_equal_zero(self):
        """Test that min_duration <= 0 raises Invalid."""
        schema = config_flow.OptionsFlowHandler.async_get_options_flow_config_schema(
            {CONF_DURATION_MODE: "flexible"}
        )

        config_data = {
            "earliest_start_time": "22:00:00",
            "latest_end_time": "06:00:00",
            "duration_mode": "flexible",
            "duration": {"hours": 2},
            "min_duration": {"hours": 0},  # min <= 0
            "price_mode": "cheapest",
            "interval_mode": "intermittent",
            "price_tolerance": 15,
        }

        with pytest.raises(vol.Invalid, match="min_duration must be greater than 0"):
            schema(config_data)

    def test_min_duration_validation_valid(self):
        """Test that valid min_duration passes."""
        schema = config_flow.OptionsFlowHandler.async_get_options_flow_config_schema(
            {CONF_DURATION_MODE: "flexible"}
        )

        config_data = {
            "earliest_start_time": "22:00:00",
            "latest_end_time": "06:00:00",
            "duration_mode": "flexible",
            "duration": {"hours": 4},
            "min_duration": {"hours": 2},
            "price_mode": "cheapest",
            "interval_mode": "intermittent",
            "price_tolerance": 15,
        }

        result = schema(config_data)
        assert result is not None

    def test_min_duration_is_required_in_flexible_mode(self):
        """Test min_duration is required (vol.Required) in flexible mode."""
        schema = config_flow.OptionsFlowHandler.async_get_options_flow_config_schema(
            {CONF_DURATION_MODE: "flexible"}
        )

        # Get the underlying schema dict
        schema_dict = schema.validators[0].schema

        # Find the key for min_duration
        min_duration_key = None
        for k in schema_dict.keys():
            if str(k) == CONF_MIN_DURATION:
                min_duration_key = k
                break

        # Check that min_duration is in the schema
        assert min_duration_key is not None

        # Check that it is vol.Required, not vol.Optional
        assert isinstance(min_duration_key, vol.Required)

    def test_validation_fails_without_min_duration_in_flexible_mode(self):
        """Test validation fails if min_duration missing in flexible mode."""
        schema = config_flow.OptionsFlowHandler.async_get_options_flow_config_schema(
            {CONF_DURATION_MODE: "flexible"}
        )

        # Config data without min_duration
        config_data = {
            "earliest_start_time": "22:00:00",
            "latest_end_time": "06:00:00",
            "duration_mode": "flexible",
            "duration": {"hours": 4},
            "price_mode": "cheapest",
            "interval_mode": "intermittent",
            "price_tolerance": 15,
        }

        # This should raise vol.Invalid because min_duration is required
        with pytest.raises(vol.Invalid):
            schema(config_data)
