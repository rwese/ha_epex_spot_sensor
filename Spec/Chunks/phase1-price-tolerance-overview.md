# Phase 1: Price Tolerance Implementation

## Overview

Implement price tolerance feature that allows users to configure acceptable price deviation (±X%) from the cheapest/most expensive price. This is Phase 1 of the "Flexible Duration with Price Tolerance" feature.

## Goals

- Add `price_tolerance` configuration parameter (0-100%, default: 0%)
- Modify contiguous interval algorithm to support tolerance
- Modify intermittent interval algorithm to support tolerance
- Apply "prefer earlier start times" secondary optimization
- Handle edge cases with graceful fallback
- Maintain 100% backward compatibility (tolerance=0 = current behavior)

## Key Design Decisions

1. **Tolerance Reference:** Relative to absolute cheapest slot (not average)
2. **Tolerance Application:** Individual slot filtering (not cumulative)
3. **Secondary Optimization:** Prefer earlier start times when multiple options exist
4. **Edge Cases:** Graceful fallback to strict ordering if insufficient slots

## Files to Modify

1. `custom_components/epex_spot_sensor/const.py` - Add constants
2. `custom_components/epex_spot_sensor/config_flow.py` - Add UI field
3. `custom_components/epex_spot_sensor/contiguous_interval.py` - Add tolerance logic
4. `custom_components/epex_spot_sensor/intermittent_interval.py` - Add tolerance logic
5. `custom_components/epex_spot_sensor/binary_sensor.py` - Pass tolerance parameter
6. `custom_components/epex_spot_sensor/translations/en.json` - Add translations

## Files to Create

1. `tests/test_price_tolerance_contiguous.py` - Unit tests for contiguous mode
2. `tests/test_price_tolerance_intermittent.py` - Unit tests for intermittent mode

## Implementation Order

1. Add configuration constants and schema
2. Implement contiguous interval tolerance
3. Implement intermittent interval tolerance
4. Update binary sensor to pass tolerance
5. Create comprehensive unit tests
6. Run all tests (including existing ones for regression)
7. Update documentation

## Success Criteria

- ✓ Configuration field added and visible in UI
- ✓ Tolerance=0% produces identical results to current behavior
- ✓ Tolerance>0% correctly filters intervals within threshold
- ✓ Earlier start times preferred when multiple options exist
- ✓ Edge cases handled gracefully
- ✓ All existing tests still pass (backward compatibility)
- ✓ New tests cover all tolerance scenarios

## Reference Documents

- Main Spec: `Spec/Backlog/flexible-duration-with-price-tolerance.md`
- Decisions: `Spec/Backlog/DECISIONS-flexible-duration-with-price-tolerance.md`
