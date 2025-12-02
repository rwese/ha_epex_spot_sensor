import logging
from datetime import datetime, timedelta


_LOGGER = logging.getLogger(__name__)

SECONDS_PER_HOUR = 60 * 60


def _find_market_price(marketdata, dt: datetime):
    for mp in marketdata:
        if dt >= mp.start_time and dt < mp.end_time:
            return mp

    return None


def _calc_interval_price(marketdata, start_time: datetime, duration: timedelta):
    """Calculate price for given start time and duration."""
    total_price = 0
    stop_time = start_time + duration

    while start_time < stop_time:
        mp = _find_market_price(marketdata, start_time)

        if mp is None:
            return None

        if mp.end_time > stop_time:
            active_duration_in_this_segment = stop_time - start_time
        else:
            active_duration_in_this_segment = mp.end_time - start_time

        total_price += (
            mp.price
            * active_duration_in_this_segment.total_seconds()
            / SECONDS_PER_HOUR
        )

        start_time = mp.end_time

    return total_price


def _calc_start_times(
    marketdata, earliest_start: datetime, latest_end: datetime, duration: timedelta
):
    """Calculate list of meaningful start times."""
    start_times = set()
    start_time = earliest_start

    # add earliest possible start (if duration matches)
    if earliest_start + duration <= latest_end:
        start_times.add(earliest_start)

    for md in marketdata:
        # add start times for market data segment start
        if md.start_time >= earliest_start and md.start_time + duration <= latest_end:
            start_times.add(earliest_start)

        # add start times for market data segment end
        start_time = md.end_time - duration
        if md.end_time <= latest_end and earliest_start <= start_time:
            start_times.add(start_time)

    # add latest possible start (if duration matches)
    start_time = latest_end - duration
    if earliest_start <= start_time:
        start_times.add(start_time)

    return sorted(start_times)


def _find_extreme_price_interval(
    marketdata,
    start_times,
    duration: timedelta,
    most_expensive: bool = False,
    price_tolerance_percent: float = 0.0,
):
    """Find the lowest/highest price for all given start times.

        The argument cmp is a lambda which is used to differentiate between
    lowest and highest price.

    Args:
        marketdata: Market price data
        start_times: List of candidate start times
        duration: Duration of the interval
        most_expensive: If True, find most expensive; otherwise find cheapest
        price_tolerance_percent: Price tolerance percentage (0.0 = no tolerance)

    Returns:
        Dict with start, end, interval_price, price_per_hour, or None if no valid interval
    """
    interval_price: float | None = None
    interval_start_time: timedelta | None = None

    if most_expensive:

        def cmp(a, b):
            return a > b

    else:

        def cmp(a, b):
            return a < b

    # Find optimal interval (cheapest or most expensive)
    for start in start_times:
        price = _calc_interval_price(marketdata, start, duration)
        if price is None:
            continue

        if interval_price is None or (
            price > interval_price if most_expensive else price < interval_price
        ):
            interval_price = price
            interval_start_time = start

    if interval_start_time is None or interval_price is None:
        return None

    # Build optimal result
    optimal_result = {
        "start": interval_start_time,
        "end": interval_start_time + duration,
        "interval_price": interval_price,
        "price_per_hour": interval_price * SECONDS_PER_HOUR / duration.total_seconds(),
    }

    # If tolerance is 0, return optimal (backward compatibility)
    if price_tolerance_percent == 0.0:
        return optimal_result

    # Calculate price threshold based on optimal price
    price_per_hour = optimal_result["price_per_hour"]

    if most_expensive:
        # For most expensive mode, threshold is lower bound
        threshold = price_per_hour * (1 - price_tolerance_percent / 100)

        def within_threshold(price):
            return price >= threshold

    else:
        # For cheapest mode, threshold is upper bound
        threshold = price_per_hour * (1 + price_tolerance_percent / 100)

        def within_threshold(price):
            return price <= threshold

    # Find all intervals within threshold
    candidates = []
    for start in start_times:
        price = _calc_interval_price(marketdata, start, duration)
        if price is None:
            continue

        price_per_hour_candidate = price * SECONDS_PER_HOUR / duration.total_seconds()

        if within_threshold(price_per_hour_candidate):
            candidates.append(
                {
                    "start": start,
                    "end": start + duration,
                    "interval_price": price,
                    "price_per_hour": price_per_hour_candidate,
                }
            )

    # If no candidates within threshold, fall back to optimal
    if len(candidates) == 0:
        _LOGGER.warning(
            "No intervals found within price tolerance (%.1f%%), "
            "using optimal interval",
            price_tolerance_percent,
        )
        return optimal_result

    # Prefer earliest start time (Decision 3)
    candidates.sort(key=lambda x: x["start"])
    return candidates[0]


def calc_interval_for_contiguous(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    duration: timedelta,
    most_expensive: bool = True,
    price_tolerance_percent: float = 0.0,
):
    if len(marketdata) == 0:
        return None

    if marketdata[-1].end_time < latest_end:
        return None

    start_times = _calc_start_times(
        marketdata,
        earliest_start=earliest_start,
        latest_end=latest_end,
        duration=duration,
    )

    start_times = sorted(list(set(start_times)))

    return _find_extreme_price_interval(
        marketdata, start_times, duration, most_expensive, price_tolerance_percent
    )
