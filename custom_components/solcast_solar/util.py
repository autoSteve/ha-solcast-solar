"""Solcast utilities."""

# pylint: disable=consider-using-enumerate
from datetime import datetime as dt, timedelta
import json
import logging
import math
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit

from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from .const import (
    ADVANCED_ALLOW_EXCEED_API_LIMIT_MAXIMUM,
    CONFIG_DISCRETE_NAME,
    CONFIG_FOLDER_DISCRETE,
    ESTIMATE,
    ESTIMATE10,
    ESTIMATE90,
)
from .enums import EnergyResult


def get_solcast_base_url(url: str, port: int) -> str:
    """Return the Solcast base URL with an optional TCP port override."""

    url = url.rstrip("/")
    if port <= 0:
        return url

    split_url = urlsplit(url)
    if not split_url.netloc:
        return url

    hostname = split_url.hostname or split_url.netloc
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"

    auth = ""
    if "@" in split_url.netloc:
        auth = f"{split_url.netloc.rsplit('@', 1)[0]}@"

    return urlunsplit(
        (
            split_url.scheme,
            f"{auth}{hostname}:{port}",
            split_url.path.rstrip("/"),
            split_url.query,
            split_url.fragment,
        )
    ).rstrip("/")


# Status code translation, HTTP and more.
# A HTTP 418 error is included here for fun. This was introduced in RFC2324#section-2.3.2 as an April Fools joke in 1998.
# A HTTP 420 error is a Demolition Man reference previously used by Twitter to indicate rate limiting, seen rarely (and oddly) by this integration.
# 400-599 = HTTP
# 900-999 = Integration-specific situation to be potentially handled with retries.
STATUS_TRANSLATE: dict[int, str] = {
    200: "Success",
    400: "Bad request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not found",
    418: "I'm a teapot",
    420: "Enhance your calm",
    429: "Try again later",
    500: "Internal web server error",
    501: "Not implemented",
    502: "Bad gateway",
    503: "Service unavailable",
    504: "Gateway timeout",
    996: "Connection refused",
    997: "Connect call failed",
    999: "Prior crash",
}

_LOGGER = logging.getLogger(__name__)


async def async_is_allow_exceed_api_limit(hass: HomeAssistant) -> bool:
    """Return whether the advanced API limit override is enabled."""

    config_dir = Path(hass.config.config_dir)
    advanced_dir = config_dir / CONFIG_DISCRETE_NAME if CONFIG_FOLDER_DISCRETE else config_dir
    advanced_file = advanced_dir / "solcast-advanced.json"
    if not advanced_file.exists():
        return False

    def _read_advanced_setting() -> bool:
        with open(advanced_file, encoding="utf-8") as f:
            data = json.load(f)
            if not isinstance(data, dict):
                return False
            value = data.get(ADVANCED_ALLOW_EXCEED_API_LIMIT_MAXIMUM, False)
            return (isinstance(value, bool) and value is True) or False

    try:
        return await hass.async_add_executor_job(_read_advanced_setting)
    except OSError, json.JSONDecodeError, ValueError:
        return False


def http_status_translate(status: int) -> str | Any:
    """Translate HTTP status code to a human-readable translation."""

    return (f"{status}/{STATUS_TRANSLATE[status]}") if STATUS_TRANSLATE.get(status) else status


def split_and_strip(value: str) -> list[str]:
    """Split a comma-separated string and strip whitespace, discarding empty items."""

    return [item.strip() for item in value.split(",") if item.strip()]


def azimuth_to_compass_degrees(azimuth: Any) -> float | None:
    """Convert Solcast azimuth to compass degrees in the range [0, 360).

    Solcast azimuth uses N=0, W=+90, E=-90, S=+/-180.
    Standard compass bearings use N=0, E=90, S=180, W=270.
    """
    try:
        return (-float(azimuth)) % 360.0
    except TypeError, ValueError:
        return None


def azimuth_to_compass_direction(azimuth: Any) -> str | None:
    """Convert an azimuth value to a 16-point cardinal compass direction."""
    if (compass_degrees := azimuth_to_compass_degrees(azimuth)) is None:
        return None

    directions = (
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSW",
        "SW",
        "WSW",
        "W",
        "WNW",
        "NW",
        "NNW",
    )
    return directions[int((compass_degrees + 11.25) // 22.5) % len(directions)]


def forecast_entry_update(forecasts: dict[dt, Any], period_start: dt, pv: float, pv10: float | None = None, pv90: float | None = None):
    """Update an individual forecast entry."""

    extant = forecasts.get(period_start)
    if extant:  # Update existing.
        forecasts[period_start][ESTIMATE] = pv
        if pv10 is not None:
            forecasts[period_start][ESTIMATE10] = pv10
        if pv90 is not None:
            forecasts[period_start][ESTIMATE90] = pv90
    elif pv10 is not None:
        forecasts[period_start] = {
            "period_start": period_start,
            "pv_estimate": pv,
            "pv_estimate10": pv10,
            "pv_estimate90": pv90,
        }
    else:
        forecasts[period_start] = {
            "period_start": period_start,
            "pv_estimate": pv,
        }


async def async_trigger_automation_by_name(hass: HomeAssistant, name: str) -> bool:
    """Trigger an automation by friendly name or entity ID; returns True if found and triggered."""
    success = False
    entity_id = None
    for state in hass.states.async_all("automation"):
        if state.entity_id == name or state.attributes.get("friendly_name") == name:
            entity_id = state.entity_id
            break
    if entity_id:
        await hass.services.async_call("automation", "trigger", {ATTR_ENTITY_ID: entity_id}, blocking=True)
        success = True
    return success


def percentile(data: list[Any], _percentile: float) -> float | int:
    """Find the given percentile in a sorted list of values."""

    if not data:
        return 0.0
    k = (len(data) - 1) * (_percentile / 100)
    f = math.floor(k)
    c = math.ceil(k)
    if f == c:
        return data[int(k)]
    d0 = data[int(f)] * (c - k)
    d1 = data[int(c)] * (k - f)
    return round(d0 + d1, 4)


def ordinal(value: int) -> str:
    """Return a number with an ordinal suffix."""

    abs_value = abs(value)
    return f"{value}{'th' if 11 <= abs_value % 100 <= 13 else {1: 'st', 2: 'nd', 3: 'rd'}.get(abs_value % 10, 'th')}"


def interquartile_bounds(sorted_data: list[Any], factor: float = 1.5) -> tuple[float | int, float | int]:
    """Return the lower and upper interquartile bounds of a sorted data set."""

    lower = 0.0
    upper = float("inf")
    iqr = 0.0
    if len(sorted_data) > 4:
        q1 = percentile(sorted_data, 25)
        q3 = percentile(sorted_data, 75)
        iqr = round(q3 - q1, 5)
        lower = round(q1 - factor * iqr, 4)
        upper = round(q3 + factor * iqr, 4)
    return (lower, upper)


def diff(lst: list[Any], non_negative: bool = True) -> list[Any]:
    """Build a numpy-like diff."""

    size = len(lst) - 1
    r: list[int | float] = [0] * size
    for i in range(size):
        r[i] = max(0, lst[i + 1] - lst[i]) if non_negative else lst[i + 1] - lst[i]
    return r


def compute_power_intervals(
    power_readings: list[tuple[dt, float]],
    generation_intervals: dict[dt, float],
) -> bool:
    """Compute time-weighted average power per 30-minute interval and add kWh to generation_intervals.

    Returns True if power readings were sufficient, False otherwise.
    """

    if len(power_readings) <= 1:
        return False

    for interval_start in generation_intervals:
        interval_end = interval_start + timedelta(minutes=30)
        weighted_sum = 0.0
        total_weight = 0.0

        for i, (reading_time, power_kw) in enumerate(power_readings):
            if i + 1 < len(power_readings):
                next_time = power_readings[i + 1][0]
            else:
                next_time = interval_end

            seg_start = max(reading_time, interval_start)
            seg_end = min(next_time, interval_end)

            if seg_start < seg_end:
                duration = (seg_end - seg_start).total_seconds()
                weighted_sum += power_kw * duration
                total_weight += duration

        if total_weight > 0:
            avg_power_kw = weighted_sum / total_weight
            generation_intervals[interval_start] += avg_power_kw * 0.5

    return True


def compute_energy_intervals(
    sample_time: list[dt],
    sample_generation: list[float],
    sample_generation_time: list[dt],
    sample_timedelta: list[int],
    generation_intervals: dict[dt, float],
    period_start: dt,
    period_end: dt,
) -> EnergyResult:
    """Distribute energy deltas across 30-minute intervals, filtering excessive jumps.

    Modifies generation_intervals in place. Returns an EnergyResult with diagnostic info.
    """

    # Determine generation-consistent or time-consistent increments.
    uniform_increment = False
    non_zero_samples = sorted([round(sample, 5) for sample in sample_generation if sample > 0.0003])
    if percentile(non_zero_samples, 25) == percentile(non_zero_samples, 75):
        uniform_increment = True
    else:
        non_zero_samples = sorted([sample for sample in sample_timedelta if sample > 0])
    _, upper = interquartile_bounds(non_zero_samples, factor=(1.5 if uniform_increment else 2.2))
    upper += 0.1 if uniform_increment else 1
    time_delta_samples = [sample for sample in sample_timedelta if sample > 0]
    if time_delta_samples:
        _, time_upper = interquartile_bounds(time_delta_samples, factor=2.2)
        time_upper += 1
    else:
        time_upper = 0

    ignored: dict[dt, bool] = {}
    last_interval: dt | None = None
    prev_report_time: dt | None = None

    if (
        len(sample_time) == len(sample_generation)
        and len(sample_time) == len(sample_generation_time)
        and len(sample_time) == len(sample_timedelta)
    ):
        for idx, (interval, kWh, report_time, time_delta) in enumerate(
            zip(sample_time, sample_generation, sample_generation_time, sample_timedelta, strict=True)
        ):
            is_excessive = False
            if interval != last_interval:
                last_interval = interval
                if uniform_increment:
                    if round(kWh, 4) > upper:
                        is_excessive = True
                        ignored[interval] = True
                elif time_delta > upper and kWh > 0.0003:
                    if kWh > 0.14:
                        is_excessive = True
                        ignored[interval] = True
                if is_excessive:
                    ignored[interval - timedelta(minutes=30)] = True

            if not is_excessive and idx > 0 and prev_report_time is not None:
                delta_start = prev_report_time
                delta_end = report_time
                current_interval_start = interval
                prev_interval_start = delta_start.replace(minute=delta_start.minute // 30 * 30, second=0, microsecond=0)

                if prev_report_time == period_start:
                    generation_intervals[current_interval_start] += kWh
                    prev_report_time = report_time
                    continue

                if report_time == period_end:
                    if prev_interval_start in generation_intervals:
                        generation_intervals[prev_interval_start] += kWh
                    prev_report_time = report_time
                    continue

                if time_upper and time_delta > time_upper and kWh > 0.0003:
                    generation_intervals[current_interval_start] += kWh
                elif prev_interval_start == current_interval_start:
                    generation_intervals[interval] += kWh
                else:
                    total_seconds = (delta_end - delta_start).total_seconds()
                    if total_seconds > 0:
                        intervals_crossed = []
                        temp_interval = prev_interval_start
                        while temp_interval <= current_interval_start:
                            interval_end = temp_interval + timedelta(minutes=30)
                            overlap_start = max(delta_start, temp_interval)
                            overlap_end = min(delta_end, interval_end)
                            if overlap_start < overlap_end:
                                overlap_seconds = (overlap_end - overlap_start).total_seconds()
                                proportion = overlap_seconds / total_seconds
                                intervals_crossed.append((temp_interval, proportion))
                            temp_interval = interval_end

                        for crossed_interval, proportion in intervals_crossed:
                            if crossed_interval in generation_intervals:
                                generation_intervals[crossed_interval] += kWh * proportion
            elif not is_excessive and idx == 0:
                generation_intervals[interval] += kWh

            prev_report_time = report_time

        for interval in ignored:
            generation_intervals[interval] = 0.0

    return EnergyResult(uniform_increment=uniform_increment, upper=upper, ignored=ignored)
