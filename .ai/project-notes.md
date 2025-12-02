# EPEX Spot Sensor - Project Notes

## Project Overview

Home Assistant integration that creates binary sensors for optimal electricity pricing schedules. Finds cheapest/most expensive time slots based on EPEX spot market data.

## Recent Changes (2025-12-02)

### ✅ Phase 1: Price Tolerance Feature - COMPLETED

Implemented price tolerance feature allowing flexible scheduling within acceptable price ranges.

#### What Was Implemented

- **Price Tolerance Configuration**: 0-100% parameter (default: 0%)
- **Contiguous Mode Support**: Filters intervals within price threshold, prefers earlier start times
- **Intermittent Mode Support**: Filters individual slots, prefers earlier times, graceful fallback
- **Binary Sensor Integration**: Passes tolerance to all interval calculations
- **Comprehensive Testing**: 23 new tests (11 contiguous + 12 intermittent)

#### Files Modified

1. `custom_components/epex_spot_sensor/const.py` - Added CONF_PRICE_TOLERANCE constant
2. `custom_components/epex_spot_sensor/config_flow.py` - Added UI field with 0-100% range
3. `custom_components/epex_spot_sensor/contiguous_interval.py` - Tolerance logic + tests
4. `custom_components/epex_spot_sensor/intermittent_interval.py` - Tolerance logic + tests
5. `custom_components/epex_spot_sensor/binary_sensor.py` - Pass tolerance parameter
6. `custom_components/epex_spot_sensor/translations/en.json` - Added translations
7. `README.md` - Updated documentation

#### Files Created

1. `tests/test_price_tolerance_contiguous.py` - 11 comprehensive tests
2. `tests/test_price_tolerance_intermittent.py` - 12 comprehensive tests
3. `Spec/Backlog/flexible-duration-with-price-tolerance.md` - Full specification
4. `Spec/Backlog/DECISIONS-flexible-duration-with-price-tolerance.md` - Design decisions
5. `Spec/Chunks/phase1-price-tolerance-overview.md` - Implementation guide
6. `Spec/Chunks/task1-config-schema.md` - Config task spec
7. `Spec/Chunks/task2-contiguous-tolerance.md` - Contiguous task spec
8. `Spec/Chunks/task3-intermittent-tolerance.md` - Intermittent task spec

#### Test Results

- **23 new tests** (11 contiguous + 12 intermittent)
- 100% backward compatibility maintained (tolerance=0 = original behavior)
- No regressions in existing functionality

#### Key Design Decisions

1. **Tolerance Reference**: Relative to absolute cheapest slot (not average)
2. **Secondary Optimization**: Prefer earlier start times when multiple options exist
3. **Tolerance Application**: Individual slot filtering (not cumulative)
4. **Edge Cases**: Graceful fallback to strict ordering if insufficient slots
5. **Performance**: No concerns due to small data sets (24-96 hourly slots)

## Architecture

### Core Components

- **binary_sensor.py**: Main entity, orchestrates interval calculations
- **contiguous_interval.py**: Finds single continuous time blocks
- **intermittent_interval.py**: Finds multiple non-contiguous slots
- **config_flow.py**: Configuration UI and validation
- **util.py**: Market data utilities

### Algorithm Flow

1. Get market price data from EPEX Spot sensor
2. Filter data to configured time window (earliest_start to latest_end)
3. Calculate optimal intervals based on mode:
   - **Contiguous**: Single block of exact duration
   - **Intermittent**: Multiple blocks summing to duration
4. Apply price tolerance filtering (if configured)
5. Prefer earlier start times among acceptable options
6. Update binary sensor state (ON if current time in interval)

### Price Tolerance Algorithm

#### Contiguous Mode

```
1. Find optimal interval (cheapest/most expensive)
2. Calculate threshold: optimal_price * (1 ± tolerance%)
3. Filter all candidate intervals within threshold
4. Sort by start time, select earliest
5. Fallback to optimal if no intervals within threshold
```

#### Intermittent Mode

```
1. Sort market data by price
2. Find reference price (first element)
3. Calculate threshold: reference_price * (1 ± tolerance%)
4. Filter slots within threshold
5. Sort filtered slots by start time (prefer earlier)
6. Select slots until duration satisfied
7. Fallback to strict price ordering if insufficient
```

## Testing Strategy

### Test Coverage

- **Unit Tests**: 57 tests covering all modes and edge cases
- **Backward Compatibility**: Default settings produce identical results to original
- **Edge Cases**: Insufficient data, threshold boundaries, fallback scenarios
- **All Modes**: Cheapest/most expensive, contiguous/intermittent, exact/flexible
- **Combined Features**: Price tolerance + flexible duration work together

### Running Tests

```bash
cd /Users/wese/Repos/ha_epex_spot_sensor
uv run pytest tests/ -v
```

### Pre-commit Hooks

```bash
pre-commit run --all-files
```

### ✅ Phase 2: Flexible Duration Feature - COMPLETED

Implemented flexible duration mode allowing "up to X hours" scheduling with minimum guarantees.

#### What Was Implemented

- **Duration Mode Configuration**: Exact/Flexible enum (default: Exact)
- **Minimum Duration Field**: Conditional field (shows only when Flexible selected)
- **Contiguous Flexible Algorithm**: Finds optimal interval between min-max duration
- **Intermittent Flexible Algorithm**: Two-phase approach (guarantee min, extend to max if prices stay low)
- **Duration Entity Override**: Entity state overrides flexible mode
- **Dynamic UI**: Conditional min_duration field based on duration_mode selection
- **Comprehensive Testing**: 18 new tests (5 contiguous + 7 intermittent + 6 config flow)

#### Files Modified (Phase 2)

1. `custom_components/epex_spot_sensor/const.py` - Added duration mode constants
2. `custom_components/epex_spot_sensor/config_flow.py` - Dynamic schema with conditional fields
3. `custom_components/epex_spot_sensor/contiguous_interval.py` - Flexible algorithm
4. `custom_components/epex_spot_sensor/intermittent_interval.py` - Flexible algorithm
5. `custom_components/epex_spot_sensor/binary_sensor.py` - Pass duration mode parameters
6. `custom_components/epex_spot_sensor/translations/en.json` - Added translations
7. `README.md` - Updated documentation with flexible mode

#### Files Created (Phase 2)

1. `tests/test_contiguous_interval_flexible.py` - 5 tests
2. `tests/test_intermittent_interval_flexible.py` - 7 tests
3. `tests/test_config_flow_flexible_duration.py` - 6 tests
4. `Spec/Chunks/issue-analysis-min-max-duration.md` - Issue analysis
5. `Spec/Chunks/regression-test-min-max-duration.md` - Regression test spec
6. `Spec/Chunks/task4-duration-mode-config.md` - Config task spec
7. `Spec/Chunks/task5-min-duration-config.md` - Min duration spec
8. `Spec/Chunks/task6-contiguous-flexible.md` - Contiguous algorithm spec
9. `Spec/Chunks/task7-intermittent-flexible.md` - Intermittent algorithm spec
10. `Spec/Chunks/task8-binary-sensor-update.md` - Binary sensor integration spec
11. `Spec/IMPLEMENTATION-SUMMARY-phase1.md` - Phase 1 summary document

#### Test Results (Combined)

- **57 tests total, all passing** (0.49s)
- Phase 1: 23 tests (price tolerance)
- Phase 2: 18 tests (flexible duration)
- Original: 16 tests (baseline functionality)
- 100% backward compatibility maintained

#### Key Design Decisions (Phase 2)

1. **Duration Entity Override**: Entity state always overrides flexible mode
2. **Contiguous Algorithm**: Find optimal interval between min-max duration
3. **Intermittent Algorithm**: Two-phase (guarantee min, extend to max within threshold)
4. **Price Threshold**: Stop adding intervals when marginal price exceeds threshold
5. **Backward Compatibility**: Default to Exact mode preserves original behavior

## Configuration

### Current Options

1. **Earliest Start Time**: When appliance can start
2. **Latest End Time**: When appliance must finish
3. **Duration**: How long appliance needs to run (max duration in Flexible mode)
4. **Remaining Duration Entity** (optional): Dynamic duration from entity (overrides flexible mode)
5. **Duration Mode** (NEW): Exact or Flexible, default Exact
6. **Minimum Duration** (NEW): Required minimum (Flexible mode only)
7. **Price Tolerance** (NEW): 0-100%, default 0%
8. **Price Mode**: Cheapest or Most Expensive
9. **Interval Mode**: Contiguous or Intermittent

### Example Configurations

#### EV Charging with Tolerance

```yaml
earliest_start_time: "22:00:00"
latest_end_time: "06:00:00"
duration: "04:00:00"
price_tolerance: 15 # Accept slots within 15% of cheapest
price_mode: cheapest
interval_mode: intermittent
```

#### Heat Pump Exact Schedule

```yaml
earliest_start_time: "00:00:00"
latest_end_time: "00:00:00" # Full 24h
duration: "03:00:00"
duration_mode: exact
price_tolerance: 0 # Strict cheapest only
price_mode: cheapest
interval_mode: contiguous
```

#### Dishwasher Flexible Duration

```yaml
earliest_start_time: "22:00:00"
latest_end_time: "06:00:00"
duration: "03:00:00" # Maximum 3 hours
duration_mode: flexible
min_duration: "01:30:00" # Minimum 1.5 hours
price_tolerance: 10 # Accept slots within 10% of cheapest
price_mode: cheapest
interval_mode: intermittent
```

## Development Notes

### Python Version

- **Required**: Python 3.13
- **Testing**: Use `uv run pytest`

### Code Style

- **Formatter**: Black
- **Linter**: Ruff
- **Type Checking**: Enabled (pyright)

### Git Workflow

1. Feature branches for new work
2. Comprehensive commit messages
3. All tests must pass before merge
4. Pre-commit hooks must pass

### Sub-Agent Pattern

This project uses sub-agents for implementation:

1. Create `Spec/Chunks/` files with detailed task specs
2. Delegate to sub-agent-coder with spec reference
3. Sub-agents implement, test, and commit
4. Orchestrator validates and coordinates

## Known Issues

None currently. All 57 tests passing.

## Dependencies

- Home Assistant Core
- EPEX Spot integration (required)
- voluptuous (schema validation)
- pytest (testing)

## Documentation

- **README.md**: User-facing documentation
- **Spec/Backlog/**: Feature specifications and decisions
- **Spec/Chunks/**: Implementation task breakdowns
- **tests/**: Comprehensive test suite with examples

## Contacts

- Repository: https://github.com/mampfes/ha_epex_spot_sensor
- EPEX Spot Integration: https://github.com/mampfes/ha_epex_spot

## Implementation Timeline

- **Phase 1 (Price Tolerance)**: Completed 2025-12-02
- **Phase 2 (Flexible Duration)**: Completed 2025-12-02
- **Total Development Time**: 1 day (both phases)
- **Final Test Count**: 57/57 passing (0.49s)

---

Last Updated: 2025-12-02 (Phase 1 & 2 Complete)
