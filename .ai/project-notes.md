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
- **39 tests total, all passing** (0.38s)
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
- **Unit Tests**: 39 tests covering all modes and edge cases
- **Backward Compatibility**: tolerance=0 produces identical results
- **Edge Cases**: Insufficient data, threshold boundaries, fallback scenarios
- **Both Modes**: Cheapest and most expensive price modes

### Running Tests
```bash
cd /Users/wese/Repos/ha_epex_spot_sensor
uv run pytest tests/ -v
```

### Pre-commit Hooks
```bash
pre-commit run --all-files
```

## Future Work (Phase 2)

### Flexible Duration Feature
**Status**: Specified, not yet implemented

**Scope**:
- Add "Duration Mode" configuration (Exact/Flexible)
- Add "Minimum Duration" field (when Flexible mode selected)
- Implement flexible contiguous algorithm
- Implement flexible intermittent algorithm
- Handle duration entity interaction
- Conditional UI for min_duration field

**Timeline**: 3-4 weeks estimated

**Reference**: See `Spec/Backlog/flexible-duration-with-price-tolerance.md`

## Configuration

### Current Options
1. **Earliest Start Time**: When appliance can start
2. **Latest End Time**: When appliance must finish
3. **Duration**: How long appliance needs to run
4. **Remaining Duration Entity** (optional): Dynamic duration from entity
5. **Price Tolerance** (NEW): 0-100%, default 0%
6. **Price Mode**: Cheapest or Most Expensive
7. **Interval Mode**: Contiguous or Intermittent

### Example Configurations

#### EV Charging with Tolerance
```yaml
earliest_start_time: "22:00:00"
latest_end_time: "06:00:00"
duration: "04:00:00"
price_tolerance: 15  # Accept slots within 15% of cheapest
price_mode: cheapest
interval_mode: intermittent
```

#### Heat Pump Exact Schedule
```yaml
earliest_start_time: "00:00:00"
latest_end_time: "00:00:00"  # Full 24h
duration: "03:00:00"
price_tolerance: 0  # Strict cheapest only
price_mode: cheapest
interval_mode: contiguous
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
None currently. All 39 tests passing.

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

---
Last Updated: 2025-12-02
