# Issue Analysis: Missing Min/Max Duration Fields

## Problem Description
User reports: "input fields for min and max duration do not show up"

## Root Cause Analysis

### What Was Implemented (Phase 1)
✅ **Price Tolerance Feature** - COMPLETED
- Added `price_tolerance` field (0-100%, default: 0%)
- Works for both contiguous and intermittent modes
- 100% backward compatible

### What Was NOT Implemented (Phase 2)
❌ **Flexible Duration Feature** - NOT YET IMPLEMENTED
- `duration_mode` dropdown (Exact/Flexible)
- `min_duration` field (conditional, only when Flexible)
- `max_duration` field (renamed from `duration` when Flexible)

### Current Configuration Schema
```python
OPTIONS_SCHEMA = vol.Schema({
    vol.Required(CONF_EARLIEST_START_TIME): selector.TimeSelector(),
    vol.Required(CONF_LATEST_END_TIME): selector.TimeSelector(),
    vol.Required(CONF_DURATION, default={"hours": 1}): selector.DurationSelector(),  # Current
    vol.Optional(CONF_DURATION_ENTITY_ID): selector.EntitySelector(...),
    vol.Required(CONF_PRICE_MODE, default=PriceModes.CHEAPEST): selector.SelectSelector(...),
    vol.Required(CONF_INTERVAL_MODE, default=IntervalModes.INTERMITTENT): selector.SelectSelector(...),
    vol.Optional(CONF_PRICE_TOLERANCE, default=0.0): selector.NumberSelector(...),  # Phase 1 ✅
    # MISSING: duration_mode, min_duration, max_duration (Phase 2 ❌)
})
```

### Issue Classification
**This is NOT a regression** - it's missing functionality that was never implemented.

**Expected vs Actual:**
- **Expected**: User sees min/max duration fields (Phase 2 features)
- **Actual**: Only price_tolerance field exists (Phase 1 only)

## Required Actions

### 1. Implement Phase 2: Flexible Duration
**Scope:**
- Add `duration_mode` configuration (Exact/Flexible)
- Add `min_duration` field (conditional on duration_mode)
- Rename `duration` to `max_duration` when Flexible mode selected
- Update UI to show/hide fields conditionally
- Implement flexible duration algorithms
- Add comprehensive tests

### 2. Configuration Schema Changes
**New Fields:**
- `CONF_DURATION_MODE` (enum: Exact/Flexible, default: Exact)
- `CONF_MIN_DURATION` (conditional field, only when Flexible)

**UI Behavior:**
- When `duration_mode = Exact`: Show `duration` field (current behavior)
- When `duration_mode = Flexible`: Show `max_duration` and `min_duration` fields

### 3. Algorithm Updates
**Contiguous Mode:** Find intervals between min_duration and max_duration
**Intermittent Mode:** Select slots until min_duration satisfied, continue up to max_duration
**Price Threshold:** Stop adding intervals when marginal price exceeds threshold

### 4. Testing Requirements
- Test conditional UI behavior
- Test flexible duration algorithms
- Test duration entity interaction
- Test backward compatibility
- Test edge cases

## Implementation Plan

### Phase 2A: Configuration Schema (2-3 days)
- Add duration_mode and min_duration constants
- Update config_flow.py with conditional fields
- Update translations
- Test UI behavior

### Phase 2B: Algorithm Implementation (3-4 days)
- Update contiguous_interval.py for flexible duration
- Update intermittent_interval.py for flexible duration
- Update binary_sensor.py to pass new parameters
- Implement price threshold stopping logic

### Phase 2C: Testing & Validation (2-3 days)
- Comprehensive unit tests
- Integration tests
- Backward compatibility verification
- Documentation updates

## Success Criteria

- ✅ Duration mode dropdown appears in UI
- ✅ Min duration field appears conditionally when Flexible selected
- ✅ Max duration field replaces Duration when Flexible selected
- ✅ Flexible algorithms work correctly
- ✅ All existing functionality preserved
- ✅ Comprehensive test coverage
- ✅ Updated documentation

## References

- Phase 2 Specification: `Spec/Backlog/flexible-duration-with-price-tolerance.md`
- Design Decisions: `Spec/Backlog/DECISIONS-flexible-duration-with-price-tolerance.md`
- Current Implementation: Phase 1 complete, Phase 2 pending
