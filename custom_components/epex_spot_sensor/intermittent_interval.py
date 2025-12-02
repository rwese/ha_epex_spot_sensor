import logging
from datetime import datetime, timedelta


_LOGGER = logging.getLogger(__name__)

SECONDS_PER_HOUR = 60 * 60


class Interval:
    def __init__(
        self,
        start_time: datetime,
        end_time: datetime,
        price: float,
        rank: int,
    ):
        self._start_time = start_time
        self._end_time = end_time
        self._price = price
        self._rank = rank

    @property
    def start_time(self):
        return self._start_time

    @property
    def end_time(self):
        return self._end_time

    @property
    def price(self):
        return self._price

    @property
    def rank(self):
        return self._rank

    def __repr__(self):
        return f"{self.__class__.__name__}(start: {self._start_time.isoformat()}, end: {self._end_time.isoformat()}, marketprice: {self._price}, rank: {self._rank})"  # noqa: E501


def calc_intervals_for_intermittent(
    marketdata,
    earliest_start: datetime,
    latest_end: datetime,
    duration: timedelta,
    most_expensive: bool = False,
    price_tolerance_percent: float = 0.0,
):
    """Calculate price for given start time and duration."""
    if len(marketdata) == 0:
        return None

    if marketdata[-1].end_time < latest_end:
        return None

    # filter intervals which fit to start- and end-time (including overlapping)
    marketdata = [
        e
        for e in marketdata
        if earliest_start < e.end_time and latest_end > e.start_time
    ]

    # sort by price
    marketdata.sort(key=lambda e: e.price, reverse=most_expensive)

    # If tolerance > 0, filter by price threshold
    if price_tolerance_percent > 0.0:
        # Reference price is the first element (cheapest or most expensive)
        reference_price = marketdata[0].price

        # Calculate threshold
        if most_expensive:
            threshold = reference_price * (1 - price_tolerance_percent / 100)
            acceptable_slots = [e for e in marketdata if e.price >= threshold]
        else:
            threshold = reference_price * (1 + price_tolerance_percent / 100)
            acceptable_slots = [e for e in marketdata if e.price <= threshold]

        # Sort acceptable slots by start time (prefer earlier)
        acceptable_slots.sort(key=lambda e: e.start_time)

        # Try to satisfy duration with acceptable slots
        test_intervals = _select_intervals_from_slots(
            acceptable_slots, earliest_start, latest_end, duration
        )

        # Check if we satisfied the duration
        total_duration = sum(
            (i.end_time - i.start_time).total_seconds() for i in test_intervals
        )

        if total_duration >= duration.total_seconds():
            # Success with tolerance
            return test_intervals
        else:
            # Fall back to strict ordering
            _LOGGER.warning(
                "Insufficient slots within price tolerance (%.1f%%), "
                "falling back to strict price ordering",
                price_tolerance_percent,
            )
            # Continue with original marketdata (sorted by price)

    # Original algorithm (or fallback)
    return _select_intervals_from_slots(
        marketdata, earliest_start, latest_end, duration
    )


def _select_intervals_from_slots(slots, earliest_start, latest_end, duration):
    """Helper function to select intervals from given slots."""
    active_time: timedelta = timedelta(seconds=0)
    intervals = []

    for count, mp in enumerate(slots):
        interval_start_time = (
            earliest_start if mp.start_time < earliest_start else mp.start_time
        )
        interval_end_time = latest_end if mp.end_time > latest_end else mp.end_time

        active_duration_in_this_segment = interval_end_time - interval_start_time

        if active_time + active_duration_in_this_segment > duration:
            # we don't need the full active_duration_in_this_segment
            active_duration_in_this_segment = duration - active_time

            # check if we can connect to an existing interval
            connects_to_next = False
            for i in intervals:
                if i.start_time == interval_end_time:
                    connects_to_next = True
                    break

            connects_to_prev = False
            for i in intervals:
                if i.end_time == interval_start_time:
                    connects_to_prev = True
                    break

            if connects_to_next and not connects_to_prev:
                # align to end
                interval_start_time = (
                    interval_end_time - active_duration_in_this_segment
                )
            else:
                # align to start
                interval_end_time = (
                    interval_start_time + active_duration_in_this_segment
                )
        else:
            # take full segment
            pass

        price = (
            mp.price
            * active_duration_in_this_segment.total_seconds()
            / SECONDS_PER_HOUR
        )

        intervals.append(
            Interval(
                start_time=interval_start_time,
                end_time=interval_start_time + active_duration_in_this_segment,
                price=price,
                rank=count,
            )
        )

        active_time += active_duration_in_this_segment

        if active_time == duration:
            break

    return intervals


def is_now_in_intervals(now: datetime, intervals):
    for e in intervals:
        if now >= e.start_time and now < e.end_time:
            return True

    return False
