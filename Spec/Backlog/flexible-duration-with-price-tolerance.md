# Backlog Item: Flexible Duration with Price Tolerance

**Status:** ✅ Ready for Implementation  
**Priority:** High  
**Type:** Feature Enhancement  
**Component:** Binary Sensor, Configuration  
**Created:** 2025-12-02  
**Decisions Finalized:** 2025-12-02  
**Decision Document:** `DECISIONS-flexible-duration-with-price-tolerance.md`

---

## Summary

Add support for flexible duration scheduling that allows the system to find optimal time intervals "up to X hours" instead of requiring exactly X hours, combined with a configurable price tolerance that permits starting around the cheapest time but allows for price deviations of ±X%.

---

## Current Behavior

The EPEX Spot Sensor currently operates with rigid duration requirements:

### Duration Handling
- **Fixed Duration:** The system always finds intervals that sum to **exactly** the configured duration
- **No Flexibility:** Both contiguous and intermittent modes require the full duration to be scheduled
- **All-or-Nothing:** If insufficient market data exists to satisfy the full duration, the sensor becomes unavailable

### Price Selection
- **Exact Cheapest:** The algorithm finds the absolute cheapest (or most expensive) time slots
- **No Tolerance:** All selected intervals are strictly ordered by price, with no flexibility
- **Greedy Selection:** In intermittent mode, slots are selected in strict price order until duration is met

### Code Locations
- **Contiguous:** `contiguous_interval.py:117-141` - `calc_interval_for_contiguous()`
- **Intermittent:** `intermittent_interval.py:40-122` - `calc_intervals_for_intermittent()`
- **Configuration:** `config_flow.py:31-64` - `OPTIONS_SCHEMA`

---

## Proposed Behavior

### Feature 1: Flexible Duration ("Up To X")

Allow users to configure a **maximum duration** with a **minimum duration** threshold, enabling the system to find optimal intervals that don't necessarily reach the maximum.

#### Configuration Options

Add new configuration parameters:

1. **Duration Mode** (new enum)
   - `EXACT` (default, current behavior)
   - `FLEXIBLE` (new mode)

2. **Minimum Duration** (new field, only visible when `FLEXIBLE` mode selected)
   - Type: Duration selector
   - Default: 50% of configured duration
   - Validation: Must be ≤ configured duration
   - Description: "Minimum required duration to complete the task"

#### Algorithm Changes

**For Contiguous Mode:**
```python
# Current: Find single interval with exact duration
# Proposed: Find best interval between min_duration and max_duration

def calc_interval_for_contiguous_flexible(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    min_duration: timedelta,
    max_duration: timedelta,
    most_expensive: bool = False,
):
    """
    Find the optimal contiguous interval between min and max duration.
    
    Strategy:
    1. Generate candidate start times (same as current)
    2. For each start time, evaluate all durations from min to max
    3. Select the interval with:
       - Lowest total cost (for cheapest mode)
       - Preference for longer durations when cost difference is negligible
    """
    pass
```

**For Intermittent Mode:**
```python
# Current: Select intervals until exact duration is reached
# Proposed: Select intervals until min_duration reached, continue up to max_duration if beneficial

def calc_intervals_for_intermittent_flexible(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    min_duration: timedelta,
    max_duration: timedelta,
    most_expensive: bool = False,
):
    """
    Find optimal intermittent intervals between min and max duration.
    
    Strategy:
    1. Sort market data by price (same as current)
    2. Select intervals until min_duration is satisfied
    3. Continue adding intervals up to max_duration if they meet price threshold
    4. Stop when max_duration reached or remaining slots too expensive
    """
    pass
```

#### Use Cases

1. **Battery Charging:** "Charge battery for up to 4 hours, but at least 2 hours during cheapest periods"
2. **Water Heating:** "Heat water up to 3 hours, minimum 1.5 hours if very cheap"
3. **Discretionary Loads:** "Run pool pump up to 6 hours, at least 3 hours during cheap periods"

---

### Feature 2: Price Tolerance

Allow users to configure a price deviation tolerance that permits selecting time slots within ±X% of the optimal price, enabling more flexible scheduling that balances cost and convenience.

#### Configuration Options

Add new configuration parameter:

1. **Price Tolerance** (new field)
   - Type: Number selector (percentage)
   - Range: 0-100%
   - Default: 0% (exact matching, current behavior)
   - Unit: Percentage
   - Description: "Allow time slots within ±X% of the cheapest/most expensive price"

#### Algorithm Changes

**Price Threshold Calculation:**
```python
def calculate_price_threshold(optimal_price: float, tolerance_percent: float, most_expensive: bool):
    """
    Calculate acceptable price range based on optimal price and tolerance.
    
    For cheapest mode:
        max_acceptable_price = optimal_price * (1 + tolerance_percent / 100)
    
    For most expensive mode:
        min_acceptable_price = optimal_price * (1 - tolerance_percent / 100)
    """
    pass
```

**For Contiguous Mode:**
```python
# Modify: _find_extreme_price_interval()
# After finding optimal interval, also consider intervals within tolerance

def _find_intervals_within_tolerance(
    marketdata,
    start_times,
    duration: timedelta,
    optimal_price: float,
    tolerance_percent: float,
    most_expensive: bool = False,
):
    """
    Find all intervals within price tolerance of optimal.
    
    Strategy:
    1. Calculate price threshold from optimal_price and tolerance
    2. Evaluate all candidate start times
    3. Return all intervals where price is within threshold
    4. Can be used for further optimization (e.g., prefer earlier/later starts)
    """
    pass
```

**For Intermittent Mode:**
```python
# Modify: calc_intervals_for_intermittent()
# Instead of strict price ordering, group slots within tolerance bands

def calc_intervals_for_intermittent_with_tolerance(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    duration: timedelta,
    tolerance_percent: float,
    most_expensive: bool = False,
):
    """
    Select intermittent intervals with price tolerance.
    
    Strategy:
    1. Find the cheapest individual slot price
    2. Calculate acceptable price threshold
    3. Filter all slots within threshold
    4. Select slots to meet duration, preferring:
       - Contiguous blocks (current behavior)
       - Earlier start times (new optimization)
       - Or user-configurable preference
    """
    pass
```

#### Price Tolerance Behavior Examples

**Scenario 1: Contiguous Mode with 10% Tolerance**
```
Market prices (EUR/MWh) for 3-hour intervals:
- 10:00-13:00: €30 (optimal, cheapest)
- 11:00-14:00: €32 (+6.7%, within tolerance)
- 12:00-15:00: €35 (+16.7%, outside tolerance)
- 14:00-17:00: €31 (+3.3%, within tolerance)

With 10% tolerance:
- Acceptable range: €30 - €33
- Valid intervals: 10:00-13:00, 11:00-14:00, 14:00-17:00
- Selection: Could choose 10:00-13:00 (cheapest) or apply secondary criteria
```

**Scenario 2: Intermittent Mode with 15% Tolerance**
```
Market prices (EUR/MWh) per hour, need 3 hours:
- 01:00-02:00: €20 (rank 0, cheapest)
- 02:00-03:00: €22 (+10%, rank 1)
- 03:00-04:00: €25 (+25%, outside tolerance)
- 14:00-15:00: €21 (+5%, rank 2)
- 23:00-00:00: €23 (+15%, rank 3, at tolerance limit)

Current behavior (0% tolerance):
- Selects: 01:00-02:00, 14:00-15:00, 02:00-03:00 (strict price order)

With 15% tolerance:
- Acceptable range: €20 - €23
- Valid slots: 01:00-02:00, 02:00-03:00, 14:00-15:00, 23:00-00:00
- Could select: 01:00-03:00, 14:00-15:00 (prefers contiguous block)
```

---

## Combined Feature: Flexible Duration + Price Tolerance

When both features are enabled together, they provide maximum flexibility:

### Example Use Case: EV Charging

**Configuration:**
- Earliest Start: 22:00
- Latest End: 06:00
- Maximum Duration: 6 hours
- Minimum Duration: 3 hours
- Price Tolerance: 20%
- Mode: Intermittent

**Behavior:**
1. Find the cheapest slots in the 22:00-06:00 window
2. Calculate acceptable price threshold (cheapest + 20%)
3. Select slots within price threshold until minimum 3 hours satisfied
4. Continue adding slots (if within threshold) up to maximum 6 hours
5. Result: Optimal balance of cost, duration, and flexibility

**Benefits:**
- Guarantees minimum charge (3 hours)
- Opportunistically charges more (up to 6 hours) if prices remain favorable
- Allows for some price flexibility to create more contiguous blocks
- Adapts to varying electricity price patterns

---

## Technical Implementation

### 1. Configuration Schema Changes

**File:** `const.py`

Add new constants:
```python
# Duration modes
CONF_DURATION_MODE = "duration_mode"

class DurationModes(Enum):
    """Duration modes for config validation."""
    EXACT = "exact"
    FLEXIBLE = "flexible"

CONF_MIN_DURATION = "min_duration"

# Price tolerance
CONF_PRICE_TOLERANCE = "price_tolerance"
DEFAULT_PRICE_TOLERANCE = 0.0
```

**File:** `config_flow.py`

Update `OPTIONS_SCHEMA`:
```python
OPTIONS_SCHEMA = vol.Schema(
    {
        # ... existing fields ...
        vol.Required(
            CONF_DURATION_MODE, default=DurationModes.EXACT
        ): selector.SelectSelector(
            selector.SelectSelectorConfig(
                translation_key=CONF_DURATION_MODE,
                mode=selector.SelectSelectorMode.LIST,
                options=[e.value for e in DurationModes],
            )
        ),
        vol.Optional(CONF_MIN_DURATION): selector.DurationSelector(),
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
        # ... rest of existing fields ...
    }
)
```

### 2. Algorithm Implementation

#### Phase 1: Price Tolerance Only (Simpler)

**Affected Files:**
- `contiguous_interval.py` - Add tolerance parameter to `_find_extreme_price_interval()`
- `intermittent_interval.py` - Add tolerance filtering to `calc_intervals_for_intermittent()`
- `binary_sensor.py` - Pass tolerance configuration to calculation functions

**Complexity:** Low-Medium
**Risk:** Low (backward compatible with tolerance=0)

#### Phase 2: Flexible Duration (More Complex)

**Affected Files:**
- `contiguous_interval.py` - New function `calc_interval_for_contiguous_flexible()`
- `intermittent_interval.py` - New function `calc_intervals_for_intermittent_flexible()`
- `binary_sensor.py` - Add duration mode logic, call appropriate functions

**Complexity:** Medium-High
**Risk:** Medium (new logic paths, needs thorough testing)

### 3. Backward Compatibility

Both features are fully backward compatible:
- **Duration Mode:** Defaults to `EXACT` (current behavior)
- **Price Tolerance:** Defaults to `0%` (current behavior)
- **Existing Configurations:** Will continue to work identically

### 4. Testing Requirements

#### Unit Tests

**New Test Files:**
- `tests/test_contiguous_interval_flexible.py`
- `tests/test_intermittent_interval_flexible.py`
- `tests/test_price_tolerance.py`

**Test Scenarios:**

1. **Flexible Duration Tests:**
   - Min = Max (equivalent to exact mode)
   - Min = 50% of Max
   - Min = 0 (fully flexible)
   - Edge cases: insufficient data for min duration

2. **Price Tolerance Tests:**
   - Tolerance = 0% (exact matching)
   - Tolerance = 10%, 20%, 50%
   - Tolerance = 100% (accepts any price)
   - Edge cases: all prices outside tolerance

3. **Combined Feature Tests:**
   - Flexible duration + price tolerance
   - Verify optimal selection with both constraints
   - Verify min duration always satisfied

4. **Backward Compatibility Tests:**
   - Default configuration produces same results as before
   - Existing test cases still pass

#### Integration Tests

1. **Binary Sensor State Tests:**
   - Sensor on/off states with flexible intervals
   - State changes when duration/tolerance updated
   - Attribute values (data, enabled, etc.)

2. **Configuration Flow Tests:**
   - UI correctly shows/hides min_duration based on duration_mode
   - Validation: min_duration ≤ duration
   - Configuration save/load with new fields

---

## User Interface Changes

### Configuration UI

**Current UI Fields:**
1. Earliest Start Time
2. Latest End Time
3. Duration
4. Remaining Duration Entity (optional)
5. Price Mode
6. Interval Mode

**Proposed UI Fields:**
1. Earliest Start Time
2. Latest End Time
3. **Duration Mode** (new dropdown: Exact / Flexible)
4. Duration (renamed to "Maximum Duration" when Flexible mode selected)
5. **Minimum Duration** (new field, only visible when Flexible mode selected)
6. Remaining Duration Entity (optional)
7. **Price Tolerance** (new percentage field)
8. Price Mode
9. Interval Mode

### Sensor Attributes

**New Attributes:**
- `duration_mode`: Reflects configured duration mode
- `min_duration`: Reflects minimum duration (if flexible mode)
- `actual_duration`: Actual scheduled duration (may differ from max in flexible mode)
- `price_tolerance`: Reflects configured price tolerance percentage
- `price_threshold`: Calculated acceptable price threshold

---

## Design Decisions ✅ FINALIZED

**All design questions have been answered. See `DECISIONS-flexible-duration-with-price-tolerance.md` for complete decision rationale.**

### 1. Flexible Duration Behavior ✅

**Decision:** **Option B** - Stop adding intervals when marginal price exceeds threshold

**Rationale:** Price-driven approach ensures cost optimization while guaranteeing minimum duration and opportunistically extending when prices remain favorable.

---

### 2. Price Tolerance Interpretation ✅

**Decision:** **Option A** - Relative to the absolute cheapest slot (±X% of minimum price)

**Rationale:** Most intuitive for users, clear reference point, predictable behavior.

**Example:** Cheapest = €20, tolerance = 10% → accept up to €22 (not €18-€22, only upward for cheapest mode)

---

### 3. Secondary Optimization Criteria ✅

**Decision:** **Option A** - Prefer earlier start times (convenience)

**Rationale:** User convenience, predictable behavior, reduces scheduling uncertainty.

---

### 4. Tolerance Application ✅

**Decision:** **Option A** - Individual slot prices (each slot within ±X% of cheapest slot)

**Rationale:** Predictable behavior, simpler implementation, prevents "expensive slot diluted by cheap slots" scenarios.

---

### 5. Dynamic Duration Entity Interaction ✅

**Decision:** **Option A** - Duration entity overrides both min and max (becomes exact duration)

**Rationale:** Simplicity, clear precedence rules. Dynamic entity represents actual need, flexible mode is for static planning.

**Documentation Note:** When "Remaining Duration Entity" is configured, flexible duration mode is disabled.

---

### 6. UI/UX Considerations ✅

**Decision:** **Option A** - Two independent features (user can enable either or both)

**Rationale:** Maximum flexibility, clear configuration, users enable only what they need.

---

### 7. Tolerance Edge Cases ✅

**Decision:** Accept recommendations

**Scenario 1** (high tolerance): Accept all slots, use secondary criteria (earliest start)  
**Scenario 2** (insufficient slots): Fall back to strict price ordering to guarantee minimum duration

**Rationale:** Prioritize reliability, graceful degradation, always satisfy minimum if possible.

---

### 8. Performance Impact ✅

**Decision:** No significant concern due to small time horizon (24-96 hourly slots)

**Approach:** Use straightforward algorithms, focus on correctness, add basic performance tests to catch regressions. 

---

## Dependencies

### Internal
- Existing price calculation functions
- Current interval selection algorithms
- Binary sensor state management
- Configuration flow system

### External
- Home Assistant: Version ≥ 2023.x (for duration selector support)
- voluptuous: Schema validation library
- Python: 3.11+ (current requirement)

---

## Success Criteria

### Feature Complete When:

1. **Configuration:**
   - ✓ Duration mode (exact/flexible) added to config flow
   - ✓ Minimum duration field appears conditionally
   - ✓ Price tolerance field added with percentage selector
   - ✓ Validation prevents invalid configurations

2. **Functionality:**
   - ✓ Flexible duration correctly finds intervals between min and max
   - ✓ Price tolerance correctly filters intervals within threshold
   - ✓ Combined mode works correctly
   - ✓ Backward compatibility maintained (defaults to exact behavior)

3. **Testing:**
   - ✓ Unit tests cover all new code paths
   - ✓ Integration tests verify binary sensor behavior
   - ✓ Edge cases handled gracefully
   - ✓ Performance acceptable with large market data sets

4. **Documentation:**
   - ✓ README updated with new configuration options
   - ✓ Examples provided for common use cases
   - ✓ Migration guide for existing users (none needed due to defaults)

5. **User Experience:**
   - ✓ Configuration UI clear and intuitive
   - ✓ Sensor attributes provide visibility into flexible decisions
   - ✓ Logging provides debugging information

---

## Risks & Mitigations

### Risk 1: Algorithm Complexity
**Impact:** High computation time with flexible duration + tolerance
**Mitigation:** 
- Implement efficient algorithms with pruning
- Add performance benchmarks to tests
- Consider async computation if needed

### Risk 2: User Confusion
**Impact:** Users don't understand how tolerance affects selection
**Mitigation:**
- Provide clear descriptions and examples in UI
- Add sensor attributes showing price threshold and actual selections
- Create comprehensive documentation with visual examples

### Risk 3: Edge Cases
**Impact:** Unexpected behavior with unusual configurations
**Mitigation:**
- Extensive unit tests covering edge cases
- Clear documentation of limitations
- Graceful fallback behavior (prefer working sub-optimally vs failing)

### Risk 4: Breaking Changes
**Impact:** New features break existing installations
**Mitigation:**
- Strict backward compatibility requirement
- Comprehensive regression testing
- Beta testing period before release

---

## Implementation Phases

### Phase 1: Price Tolerance Only (Recommended First)
**Scope:** Add price tolerance feature only
**Rationale:** Simpler to implement, provides immediate value, lower risk
**Duration:** 1-2 weeks

**Deliverables:**
- Price tolerance configuration field
- Modified interval selection algorithms
- Unit tests for price tolerance
- Updated documentation

### Phase 2: Flexible Duration
**Scope:** Add flexible duration feature
**Rationale:** More complex, builds on Phase 1 experience
**Duration:** 2-3 weeks

**Deliverables:**
- Duration mode configuration
- Minimum duration field
- New flexible interval algorithms
- Unit tests for flexible duration
- Updated documentation

### Phase 3: Combined Optimization
**Scope:** Optimize combined feature behavior
**Rationale:** Fine-tune how features interact
**Duration:** 1 week

**Deliverables:**
- Performance optimizations
- Enhanced secondary selection criteria
- Integration tests
- User guide with examples

---

## Related Issues

*(To be filled in if GitHub issues exist)*

---

## Notes

### Design Decisions

1. **Why Percentage-Based Tolerance?**
   - More intuitive for users ("within 10% of cheapest")
   - Scales appropriately with price levels
   - Alternative (absolute tolerance) considered but rejected due to varying price ranges

2. **Why Separate Features?**
   - Users may want only one feature (flexibility vs tolerance)
   - Easier to test and debug independently
   - Clearer configuration options

3. **Why Default to Current Behavior?**
   - Ensures existing users see no changes
   - Explicit opt-in for new behavior
   - Reduces upgrade risk

### Future Enhancements

Potential follow-up features (not in scope for this backlog item):

1. **Time-of-Day Preferences:** Weight earlier/later slots differently
2. **Contiguity Preferences:** Penalize fragmented schedules in intermittent mode
3. **Multiple Duration Targets:** Support multiple appliances with dependencies
4. **Forecasting Integration:** Use price forecasts to make better decisions
5. **Learning Mode:** Adapt min/max duration based on actual consumption patterns

---

## Appendix: Algorithm Pseudocode

### Flexible Duration - Contiguous Mode

```python
def calc_interval_for_contiguous_flexible(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    min_duration: timedelta,
    max_duration: timedelta,
    tolerance_percent: float = 0.0,
    most_expensive: bool = False,
):
    # Step 1: Find optimal interval for max_duration
    optimal_result = calc_interval_for_contiguous(
        marketdata, earliest_start, latest_end, max_duration, most_expensive
    )
    
    if optimal_result is None:
        # Can't satisfy max, try min
        return calc_interval_for_contiguous(
            marketdata, earliest_start, latest_end, min_duration, most_expensive
        )
    
    # Step 2: If tolerance is 0, return optimal
    if tolerance_percent == 0:
        return optimal_result
    
    # Step 3: Calculate price threshold
    threshold = optimal_result["price_per_hour"] * (1 + tolerance_percent / 100)
    if most_expensive:
        threshold = optimal_result["price_per_hour"] * (1 - tolerance_percent / 100)
    
    # Step 4: Find all intervals between min and max duration within threshold
    candidates = []
    for duration in iterate_durations(min_duration, max_duration):
        result = calc_interval_for_contiguous(
            marketdata, earliest_start, latest_end, duration, most_expensive
        )
        if result and is_within_threshold(result["price_per_hour"], threshold, most_expensive):
            candidates.append(result)
    
    # Step 5: Select best candidate (prefer longer duration if price similar)
    return select_best_candidate(candidates, prefer_longer=True)
```

### Flexible Duration - Intermittent Mode

```python
def calc_intervals_for_intermittent_flexible(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    min_duration: timedelta,
    max_duration: timedelta,
    tolerance_percent: float = 0.0,
    most_expensive: bool = False,
):
    # Step 1: Filter and sort market data by price
    filtered_data = filter_market_data(marketdata, earliest_start, latest_end)
    sorted_data = sorted(filtered_data, key=lambda e: e.price, reverse=most_expensive)
    
    # Step 2: Find the reference price (cheapest/most expensive slot)
    reference_price = sorted_data[0].price
    
    # Step 3: Calculate price threshold
    threshold = reference_price * (1 + tolerance_percent / 100)
    if most_expensive:
        threshold = reference_price * (1 - tolerance_percent / 100)
    
    # Step 4: Filter slots within tolerance
    acceptable_slots = [
        slot for slot in sorted_data
        if is_within_threshold(slot.price, threshold, most_expensive)
    ]
    
    # Step 5: Select slots until min_duration satisfied (strict price order)
    intervals = []
    active_time = timedelta(0)
    
    for slot in sorted_data:  # Use strict ordering for minimum
        if active_time >= min_duration:
            break
        interval, duration = create_interval_from_slot(slot, earliest_start, latest_end)
        intervals.append(interval)
        active_time += duration
    
    # Step 6: Continue adding acceptable slots up to max_duration (with tolerance)
    for slot in acceptable_slots:
        if active_time >= max_duration:
            break
        if slot not in already_selected(intervals):
            interval, duration = create_interval_from_slot(slot, earliest_start, latest_end)
            if active_time + duration <= max_duration:
                intervals.append(interval)
                active_time += duration
    
    # Step 7: Optimize for contiguity
    intervals = merge_contiguous_intervals(intervals)
    
    return intervals
```

---

## Appendix: Configuration Examples

### Example 1: EV Charging (Flexible Duration + Tolerance)

```yaml
# Configuration
name: "EV Charger Optimal"
entity_id: sensor.epex_spot_de
earliest_start_time: "22:00:00"
latest_end_time: "06:00:00"
duration_mode: flexible
duration: "06:00:00"  # max 6 hours
min_duration: "03:00:00"  # min 3 hours
price_tolerance: 20  # within 20% of cheapest
price_mode: cheapest
interval_mode: intermittent
```

### Example 2: Heat Pump (Exact Duration + Tolerance)

```yaml
# Configuration
name: "Heat Pump Smart Schedule"
entity_id: sensor.epex_spot_de
earliest_start_time: "00:00:00"
latest_end_time: "00:00:00"  # full 24h
duration_mode: exact
duration: "04:00:00"  # exactly 4 hours
price_tolerance: 15  # within 15% of cheapest
price_mode: cheapest
interval_mode: contiguous
```

### Example 3: Pool Pump (Flexible Duration, No Tolerance)

```yaml
# Configuration
name: "Pool Pump Efficient"
entity_id: sensor.epex_spot_de
earliest_start_time: "10:00:00"
latest_end_time: "18:00:00"
duration_mode: flexible
duration: "04:00:00"  # max 4 hours
min_duration: "02:00:00"  # min 2 hours
price_tolerance: 0  # strict cheapest only
price_mode: cheapest
interval_mode: intermittent
```

---

**End of Backlog Specification**
