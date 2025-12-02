# Design Decisions: Flexible Duration with Price Tolerance

**Date:** 2025-12-02  
**Status:** ✅ Approved  
**Related Spec:** `flexible-duration-with-price-tolerance.md`

---

## Summary

This document captures the finalized design decisions for the Flexible Duration with Price Tolerance feature. All open questions have been answered and the specification is ready for implementation.

---

## Decision Record

### ✅ Decision 1: Flexible Duration Behavior

**Question:** When duration is flexible (e.g., min=2h, max=4h), what should the selection criteria be?

**Decision:** **Option B** - Stop adding intervals when marginal price exceeds threshold

**Rationale:**

- Price-driven approach ensures cost optimization
- Natural stopping point when prices become unfavorable
- Balances between minimum guarantee and opportunistic extension
- Aligns with user intent: "run longer if it's still cheap"

**Implementation Impact:**

- Algorithm continues adding slots after min_duration is satisfied
- Each additional slot is evaluated against price threshold
- Stops when: (a) max_duration reached, or (b) next slot exceeds threshold
- Ensures min_duration is always satisfied first (strict price ordering)

---

### ✅ Decision 2: Price Tolerance Interpretation

**Question:** Should price tolerance be relative to cheapest slot, average, median, or user-configurable?

**Decision:** **Option A** - Relative to the absolute cheapest slot (±X% of minimum price)

**Rationale:**

- Most intuitive for users: "within 10% of the cheapest price"
- Clear reference point (the optimal price)
- Predictable behavior
- Scales appropriately with price levels

**Implementation Impact:**

```python
# For cheapest mode:
reference_price = min(slot.price for slot in marketdata)
max_acceptable_price = reference_price * (1 + tolerance_percent / 100)

# For most expensive mode:
reference_price = max(slot.price for slot in marketdata)
min_acceptable_price = reference_price * (1 - tolerance_percent / 100)
```

**Example:**

- Cheapest slot: €20/MWh
- Tolerance: 10%
- Acceptable range: €20 - €22/MWh (not €18-€22)
- Note: Only upward tolerance for cheapest mode (don't need cheaper than cheapest!)

---

### ✅ Decision 3: Secondary Optimization Criteria

**Question:** When multiple intervals satisfy price tolerance, how to choose?

**Decision:** **Option A** - Prefer earlier start times (convenience)

**Rationale:**

- User convenience: earlier completion is generally preferred
- Predictable behavior: users know system will start as early as possible
- Reduces uncertainty in scheduling
- Aligns with typical user expectations

**Implementation Impact:**

- When multiple candidate intervals have similar prices (within tolerance):
  - Sort by start time (ascending)
  - Select earliest qualifying interval
- For intermittent mode:
  - Among slots with acceptable prices, prefer earlier slots
  - Maintain contiguity optimization (existing behavior)
  - Use start time as tiebreaker

**Example:**

```
Three 3-hour intervals within 10% tolerance:
- 01:00-04:00: €21 total
- 10:00-13:00: €20 total (cheapest)
- 14:00-17:00: €21.50 total

Selection: 01:00-04:00 (earliest, even though not absolute cheapest)
```

---

### ✅ Decision 4: Tolerance Application

**Question:** In intermittent mode, should tolerance apply to individual slots or cumulative average?

**Decision:** **Option A** - Individual slot prices (each slot within ±X% of cheapest slot)

**Rationale:**

- Predictable behavior: users can understand which slots qualify
- Simpler implementation
- Avoids complex averaging calculations
- Prevents "expensive slot diluted by cheap slots" scenarios

**Implementation Impact:**

```python
# Filter slots individually
reference_price = min(slot.price for slot in marketdata)
threshold = reference_price * (1 + tolerance_percent / 100)

acceptable_slots = [
    slot for slot in marketdata
    if slot.price <= threshold
]

# Then select from acceptable_slots to meet duration
```

**Example:**

```
Hourly prices, need 3 hours, 15% tolerance:
- 01:00: €20 (cheapest, reference)
- 02:00: €22 (+10%, acceptable)
- 03:00: €25 (+25%, rejected)
- 14:00: €23 (+15%, acceptable, at limit)

Acceptable slots: 01:00, 02:00, 14:00
Selection: 01:00, 02:00, 14:00 (3 hours total)
```

---

### ✅ Decision 5: Dynamic Duration Entity Interaction

**Question:** How should flexible duration interact with dynamic duration entities?

**Decision:** **Option A** - Duration entity overrides both min and max (becomes exact duration)

**Rationale:**

- Simplicity: clear precedence rules
- Dynamic entity represents actual need (e.g., remaining battery charge)
- Flexible mode is for static planning scenarios
- Avoids complex interactions and edge cases

**Implementation Impact:**

- When `duration_entity_id` is set AND has valid state:
  - Ignore `duration_mode`, `min_duration`, and `max_duration` config
  - Use entity value as exact duration (current behavior)
  - Log info message: "Duration entity active, flexible mode disabled"
- When `duration_entity_id` is not set OR unavailable:
  - Use configured duration mode (exact/flexible)
  - Apply min/max duration if flexible mode

**Documentation Note:**
Add to README:

> **Note:** When a "Remaining Duration Entity" is configured, the flexible duration mode is disabled and the entity value is used as an exact duration requirement. Flexible duration mode only applies to static duration configurations.

---

### ✅ Decision 6: UI/UX Considerations

**Question:** Should features be presented as independent, combined, or with recommendations?

**Decision:** **Option A** - Two independent features (user can enable either or both)

**Rationale:**

- Maximum flexibility for users
- Clear configuration options
- Users can enable only what they need
- Easier to understand and document

**Implementation Impact:**

- Configuration UI shows all options independently:
  - Duration Mode (dropdown: Exact / Flexible)
  - Minimum Duration (conditional field)
  - Price Tolerance (percentage field, always visible)
- No complex interdependencies in UI
- Each feature has clear on/off state

**UI Layout:**

```
┌─────────────────────────────────────┐
│ Earliest Start Time: [22:00]        │
│ Latest End Time: [06:00]            │
│                                     │
│ Duration Mode: [Exact ▼]           │
│ Duration: [04:00:00]                │
│ (Minimum Duration: hidden)          │
│                                     │
│ Price Tolerance: [10] %             │
│                                     │
│ Price Mode: [Cheapest ▼]           │
│ Interval Mode: [Intermittent ▼]    │
└─────────────────────────────────────┘

When Duration Mode = Flexible:
┌─────────────────────────────────────┐
│ Duration Mode: [Flexible ▼]        │
│ Maximum Duration: [04:00:00]        │
│ Minimum Duration: [02:00:00]        │
└─────────────────────────────────────┘
```

---

### ✅ Decision 7: Tolerance Edge Cases

**Question:** How to handle edge cases where tolerance creates conflicts?

**Decision:** **Accept Recommendations**

- **Scenario 1** (high tolerance): Accept all slots within window, use secondary criteria (earliest start time) to select
- **Scenario 2** (insufficient slots): Fall back to strict price ordering to guarantee minimum duration

**Rationale:**

- Prioritize reliability: always satisfy minimum duration if possible
- Graceful degradation: fall back to strict mode rather than fail
- User expectation: "at least give me the minimum, even if not within tolerance"

**Implementation Impact:**

**Scenario 1: Tolerance accepts all slots**

```python
if len(acceptable_slots) >= total_slots_in_window:
    # All slots acceptable, use secondary criteria
    # Sort by start time (Decision 3)
    acceptable_slots.sort(key=lambda s: s.start_time)
    # Select earliest slots to meet duration
```

**Scenario 2: Insufficient slots within tolerance**

```python
# Try to satisfy min_duration with tolerance
selected_slots = select_from_acceptable_slots(acceptable_slots, min_duration)

if total_duration(selected_slots) < min_duration:
    # Fall back to strict price ordering
    _LOGGER.warning(
        "Insufficient slots within price tolerance (%.1f%%), "
        "falling back to strict price ordering to satisfy minimum duration",
        tolerance_percent
    )
    # Use original algorithm (no tolerance)
    selected_slots = select_strict_price_order(all_slots, min_duration)
```

**User Visibility:**

- Log warnings when fallback occurs
- Sensor attribute `price_tolerance_satisfied: false` when fallback used
- Helps users adjust tolerance if needed

---

### ✅ Decision 8: Performance Impact

**Question:** Will these features significantly impact calculation performance?

**Decision:** **No significant concern** - Due to the small time horizon (typically 24-48 hours of market data), performance impact is negligible

**Rationale:**

- Market data is typically 24-96 hourly slots
- Even with O(n²) algorithms, n is small (< 100)
- Modern hardware handles this trivially
- No need for complex optimizations

**Implementation Impact:**

- Use straightforward, readable algorithms
- No need for caching or complex optimizations
- Focus on correctness over performance
- Add basic performance tests to catch regressions

**Performance Tests:**

```python
def test_performance_large_dataset():
    """Test with 168 hours (1 week) of market data."""
    marketdata = generate_market_data(hours=168)

    start_time = time.time()
    result = calc_intervals_for_intermittent_flexible(
        marketdata, ..., tolerance_percent=20
    )
    elapsed = time.time() - start_time

    assert elapsed < 0.1  # Should complete in < 100ms
```

---

## Implementation Priority

Based on decisions, recommended implementation order:

### Phase 1: Price Tolerance (2-3 weeks)

**Rationale:** Simpler feature, provides immediate value, lower risk

**Scope:**

1. Add `CONF_PRICE_TOLERANCE` configuration (Decision 2)
2. Implement tolerance filtering for contiguous mode (Decision 4)
3. Implement tolerance filtering for intermittent mode (Decision 4)
4. Apply secondary optimization (Decision 3: prefer earlier)
5. Handle edge cases (Decision 7)
6. Unit tests + integration tests
7. Documentation

**Deliverables:**

- Users can set price tolerance 0-100%
- System finds intervals within tolerance of cheapest price
- Prefers earlier start times when multiple options exist
- Graceful fallback when tolerance too restrictive

### Phase 2: Flexible Duration (3-4 weeks)

**Rationale:** More complex, builds on Phase 1 experience

**Scope:**

1. Add `CONF_DURATION_MODE` and `CONF_MIN_DURATION` (Decision 1)
2. Implement flexible contiguous algorithm (Decision 1)
3. Implement flexible intermittent algorithm (Decision 1)
4. Handle dynamic entity interaction (Decision 5)
5. UI conditional field display (Decision 6)
6. Unit tests + integration tests
7. Documentation

**Deliverables:**

- Users can select Exact or Flexible duration mode
- System finds intervals between min and max duration
- Stops adding intervals when price exceeds threshold
- Dynamic duration entity overrides flexible mode

### Phase 3: Polish & Optimization (1 week)

**Scope:**

1. Combined feature testing (both enabled)
2. Performance validation (Decision 8)
3. User documentation with examples
4. Edge case refinement
5. Beta testing feedback

---

## Configuration Examples with Decisions Applied

### Example 1: EV Charging (Both Features)

```yaml
name: "EV Charger Smart"
entity_id: sensor.epex_spot_de
earliest_start_time: "22:00:00"
latest_end_time: "06:00:00"
duration_mode: flexible # Decision 1
duration: "06:00:00" # max 6 hours
min_duration: "03:00:00" # min 3 hours
price_tolerance: 20 # Decision 2: within 20% of cheapest
price_mode: cheapest
interval_mode: intermittent
```

**Behavior:**

1. Find cheapest slot in 22:00-06:00 window (e.g., €15/MWh at 02:00)
2. Calculate threshold: €15 × 1.20 = €18/MWh (Decision 2)
3. Filter all slots ≤ €18/MWh (Decision 4)
4. Select slots in price order until min 3h satisfied (Decision 1)
5. Continue adding slots (if ≤ €18) up to max 6h (Decision 1)
6. Among acceptable slots, prefer earlier times (Decision 3)
7. Result: Might select 02:00-05:00 (3h) if prices rise, or 02:00-08:00 (6h) if prices stay low

### Example 2: Heat Pump (Tolerance Only)

```yaml
name: "Heat Pump Efficient"
entity_id: sensor.epex_spot_de
earliest_start_time: "00:00:00"
latest_end_time: "00:00:00" # full 24h
duration_mode: exact # Decision 6: independent feature
duration: "04:00:00" # exactly 4 hours
price_tolerance: 15 # Decision 2: within 15% of cheapest
price_mode: cheapest
interval_mode: contiguous
```

**Behavior:**

1. Find cheapest 4-hour contiguous block (e.g., 02:00-06:00 at €80 total)
2. Calculate threshold: €20/h × 1.15 = €23/h (Decision 2)
3. Find all 4-hour blocks with avg ≤ €23/h (Decision 4)
4. Select earliest qualifying block (Decision 3)
5. Result: Might select 01:00-05:00 if within tolerance and earlier

### Example 3: Pool Pump (Flexible Only)

```yaml
name: "Pool Pump Flexible"
entity_id: sensor.epex_spot_de
earliest_start_time: "09:00:00"
latest_end_time: "17:00:00"
duration_mode: flexible # Decision 1
duration: "04:00:00" # max 4 hours
min_duration: "02:00:00" # min 2 hours
price_tolerance: 0 # Decision 6: independent, disabled
price_mode: cheapest
interval_mode: intermittent
```

**Behavior:**

1. Sort all slots 09:00-17:00 by price (strict ordering, no tolerance)
2. Select cheapest slots until min 2h satisfied (Decision 1)
3. Continue adding slots (in price order) up to max 4h (Decision 1)
4. Stop when: next slot significantly more expensive OR max reached (Decision 1)
5. Result: Runs 2-4 hours depending on price distribution

---

## Testing Strategy Based on Decisions

### Unit Tests

**Price Tolerance Tests:**

```python
def test_tolerance_relative_to_cheapest():
    """Decision 2: Tolerance relative to cheapest slot."""
    # Cheapest slot: €20, tolerance: 10%
    # Should accept slots up to €22, not below €18

def test_tolerance_individual_slots():
    """Decision 4: Apply tolerance to individual slots."""
    # Each slot evaluated independently against threshold

def test_tolerance_prefers_earlier():
    """Decision 3: Prefer earlier start times."""
    # Multiple intervals within tolerance, select earliest

def test_tolerance_edge_case_all_acceptable():
    """Decision 7: Handle high tolerance gracefully."""
    # Tolerance 100%, all slots acceptable, use secondary criteria

def test_tolerance_edge_case_insufficient():
    """Decision 7: Fall back to strict ordering."""
    # Tolerance too low, fall back to guarantee min duration
```

**Flexible Duration Tests:**

```python
def test_flexible_stops_at_price_threshold():
    """Decision 1: Stop when marginal price exceeds threshold."""
    # Min 2h, max 4h, prices rise after 3h
    # Should select 3h (between min and max)

def test_flexible_with_duration_entity():
    """Decision 5: Duration entity overrides flexible mode."""
    # Flexible configured, but entity present
    # Should use entity value as exact duration

def test_flexible_maximizes_within_threshold():
    """Decision 1: Opportunistically extend to max."""
    # Min 2h, max 4h, all slots cheap
    # Should select full 4h
```

**Combined Tests:**

```python
def test_combined_flexible_and_tolerance():
    """Both features enabled, verify interaction."""
    # Flexible duration + price tolerance
    # Should satisfy min, extend within tolerance, prefer earlier
```

---

## Documentation Updates Required

### README.md Additions

**Section: Configuration Options**

Add after existing options:

```markdown
7. Duration Mode (optional, default: Exact)
   Select whether to use exact or flexible duration:

   - **Exact**: Find intervals totaling exactly the configured duration (current behavior)
   - **Flexible**: Find intervals between minimum and maximum duration, stopping when prices exceed threshold

8. Minimum Duration (optional, only when Duration Mode = Flexible)
   Minimum required duration when using flexible mode. Must be less than or equal to Duration.
   Example: Set Duration to 6 hours and Minimum Duration to 3 hours to run "3-6 hours depending on prices"

9. Price Tolerance (optional, default: 0%)
   Allow time slots within ±X% of the cheapest/most expensive price.

   - 0% = Exact cheapest/most expensive (current behavior)
   - 10% = Accept slots within 10% of optimal price
   - Higher values = More flexibility in scheduling

   Example: If cheapest slot is €20/MWh and tolerance is 15%, slots up to €23/MWh are acceptable.
```

**Section: Use Cases**

Add new section:

```markdown
## Advanced Use Cases

### Flexible EV Charging

Configure your EV charger to charge "at least 3 hours, up to 6 hours" during the cheapest periods:

- Duration Mode: Flexible
- Duration: 6 hours (maximum)
- Minimum Duration: 3 hours (guaranteed minimum)
- Price Tolerance: 20% (accept slots within 20% of cheapest)

The system will guarantee at least 3 hours of charging during cheap periods, and opportunistically extend up to 6 hours if prices remain favorable.

### Flexible Heat Pump with Tolerance

Run your heat pump for exactly 4 hours, but allow some flexibility in timing:

- Duration Mode: Exact
- Duration: 4 hours
- Price Tolerance: 15% (accept slots within 15% of cheapest)

The system will find a 4-hour window that's within 15% of the absolute cheapest option, preferring earlier start times when multiple options exist.
```

---

## Risk Mitigation Based on Decisions

### Risk 1: User Confusion About Tolerance

**Mitigation:**

- Clear UI labels: "Accept prices within X% of cheapest"
- Sensor attribute shows actual threshold: `price_threshold: €23/MWh`
- Sensor attribute shows if tolerance was satisfied: `price_tolerance_satisfied: true`
- Documentation with visual examples

### Risk 2: Unexpected Behavior with High Tolerance

**Mitigation:**

- Decision 7: Graceful handling of edge cases
- Logging when all slots are acceptable
- Secondary criteria (Decision 3) provides predictable selection

### Risk 3: Flexible Duration Confusion

**Mitigation:**

- Clear naming: "Minimum Duration" and "Maximum Duration" (when flexible)
- Sensor attribute shows actual scheduled duration: `actual_duration: 3:30:00`
- Decision 5: Clear precedence when duration entity present

### Risk 4: Performance Concerns

**Mitigation:**

- Decision 8: Acknowledged as non-issue for typical use cases
- Add performance tests to catch regressions
- Simple, readable algorithms (no premature optimization)

---

## Success Metrics

### Phase 1 (Price Tolerance) Complete When:

- ✓ Users can configure tolerance 0-100%
- ✓ Intervals selected within tolerance of cheapest price (Decision 2)
- ✓ Earlier start times preferred (Decision 3)
- ✓ Individual slot filtering works (Decision 4)
- ✓ Edge cases handled gracefully (Decision 7)
- ✓ All unit tests pass
- ✓ Documentation updated

### Phase 2 (Flexible Duration) Complete When:

- ✓ Users can select Exact/Flexible mode
- ✓ Minimum duration always satisfied
- ✓ Stops adding intervals at price threshold (Decision 1)
- ✓ Duration entity overrides flexible mode (Decision 5)
- ✓ UI conditionally shows min_duration field (Decision 6)
- ✓ All unit tests pass
- ✓ Documentation updated

### Phase 3 (Combined) Complete When:

- ✓ Both features work together correctly
- ✓ Performance acceptable (Decision 8)
- ✓ Edge cases handled
- ✓ User documentation with examples
- ✓ Beta testing feedback addressed

---

## Open Items (None)

All design questions have been answered. Specification is ready for implementation.

---

**Approved By:** User  
**Date:** 2025-12-02  
**Next Step:** Begin Phase 1 implementation (Price Tolerance)
