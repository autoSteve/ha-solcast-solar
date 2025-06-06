"""Tests setup for Solcast Solar integration."""

import copy
import logging
from pathlib import Path
import re
from re import Pattern
from typing import Any
from zoneinfo import ZoneInfo

from aiohttp import ClientConnectionError
from yarl import URL

from homeassistant.components.solcast_solar import const
from homeassistant.components.solcast_solar.const import (
    API_QUOTA,
    AUTO_UPDATE,
    BRK_ESTIMATE,
    BRK_ESTIMATE10,
    BRK_ESTIMATE90,
    BRK_HALFHOURLY,
    BRK_HOURLY,
    BRK_SITE,
    BRK_SITE_DETAILED,
    CONFIG_VERSION,
    CUSTOM_HOUR_SENSOR,
    DOMAIN,
    EXCLUDE_SITES,
    HARD_LIMIT_API,
    KEY_ESTIMATE,
    SITE_DAMP,
)
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .aioresponses import CallbackResult, aioresponses
from .simulator import API_KEY_SITES, SimulatedSolcast

from tests.common import MockConfigEntry

KEY1 = "1"
KEY2 = "2"
KEY_NO_SITES = "no_sites"
CUSTOM_HOURS = 2
DEFAULT_INPUT1_NO_DAMP: dict[str, Any] = {
    CONF_API_KEY: KEY1,
    API_QUOTA: "20",
    AUTO_UPDATE: "1",
    CUSTOM_HOUR_SENSOR: CUSTOM_HOURS,
    HARD_LIMIT_API: "100.0",
    KEY_ESTIMATE: "estimate",
    BRK_ESTIMATE: True,
    BRK_ESTIMATE10: False,
    BRK_ESTIMATE90: False,
    BRK_SITE: False,
    BRK_HALFHOURLY: False,
    BRK_HOURLY: False,
    BRK_SITE_DETAILED: False,
    EXCLUDE_SITES: [],
}

BAD_INPUT = copy.deepcopy(DEFAULT_INPUT1_NO_DAMP)
BAD_INPUT[CONF_API_KEY] = "badkey"

SITE_DAMP_FACTORS: dict[str, float] = {f"damp{factor:02d}": 1.0 for factor in range(24)}
DEFAULT_INPUT1 = DEFAULT_INPUT1_NO_DAMP | SITE_DAMP_FACTORS | {SITE_DAMP: False}
ZONE_RAW = "Australia/Brisbane"  # Somewhere without daylight saving time by default

DEFAULT_INPUT2 = copy.deepcopy(DEFAULT_INPUT1)
DEFAULT_INPUT2[CONF_API_KEY] = KEY1 + "," + KEY2
DEFAULT_INPUT2[AUTO_UPDATE] = 2
DEFAULT_INPUT2[BRK_HOURLY] = True
DEFAULT_INPUT2[BRK_HALFHOURLY] = True
DEFAULT_INPUT2[BRK_ESTIMATE] = False
DEFAULT_INPUT2[BRK_ESTIMATE10] = True
DEFAULT_INPUT2[BRK_ESTIMATE90] = True
DEFAULT_INPUT2[BRK_SITE_DETAILED] = True
DEFAULT_INPUT2[BRK_SITE] = True
DEFAULT_INPUT2[HARD_LIMIT_API] = "12,6"

DEFAULT_INPUT_NO_SITES = copy.deepcopy(DEFAULT_INPUT1)
DEFAULT_INPUT_NO_SITES[CONF_API_KEY] = KEY_NO_SITES

STATUS_401: dict[str, Any] = {
    "response_status": {
        "error_code": "InvalidApiKey",
        "message": "The API key is invalid.",
        "errors": [],
    }
}
STATUS_403: dict[str, Any] = {
    "response_status": {
        "error_code": "Forbidden",
        "message": "The request cannot be made using this API key.",
        "errors": [],
    }
}
STATUS_EMPTY = ""
STATUS_429_OVER: dict[str, Any] = {
    "response_status": {
        "error_code": "TooManyRequests",
        "message": "You have exceeded your free daily limit.",
        "errors": [],
    }
}
STATUS_429_UNEXPECTED: dict[str, Any] = {
    "response_status": {
        "error_code": "NoIdea",
        "message": "I have no idea what you want, but I am busy.",
        "errors": [],
    }
}

MOCK_BAD_REQUEST = "return_400"
MOCK_BUSY = "return_429"
MOCK_BUSY_SITE = "return_429_for_site"
MOCK_BUSY_UNEXPECTED = "return_429_unexpected"
MOCK_CORRUPT_SITES = "return_corrupt_sites"
MOCK_CORRUPT_FORECAST = "return_corrupt_forecast"
MOCK_CORRUPT_ACTUALS = "return_corrupt_actuals"
MOCK_EXCEPTION = "exception"
MOCK_FORBIDDEN = "return_403"
MOCK_NOT_FOUND = "return_404"
MOCK_OVER_LIMIT = "return_429_over"

MOCK_SESSION_CONFIG: dict[str, Any] = {
    "aioresponses": None,
    "api_limit": int(min(DEFAULT_INPUT2[API_QUOTA].split(","))),
    "api_used": {api_key: 0 for api_key in DEFAULT_INPUT2[CONF_API_KEY].split(",")},
    MOCK_BAD_REQUEST: False,
    MOCK_BUSY: False,
    MOCK_BUSY_SITE: None,
    MOCK_BUSY_UNEXPECTED: False,
    MOCK_CORRUPT_SITES: False,
    MOCK_CORRUPT_FORECAST: False,
    MOCK_CORRUPT_ACTUALS: False,
    MOCK_EXCEPTION: None,
    MOCK_FORBIDDEN: False,
    MOCK_NOT_FOUND: False,
    MOCK_OVER_LIMIT: False,
}

_LOGGER = logging.getLogger(__name__)

simulated: SimulatedSolcast = SimulatedSolcast()


def _check_abend(api_key: str, site: str | None = None) -> CallbackResult | None:
    if MOCK_SESSION_CONFIG[MOCK_BUSY] or (MOCK_SESSION_CONFIG[MOCK_BUSY_SITE] and site == MOCK_SESSION_CONFIG[MOCK_BUSY_SITE]):
        return CallbackResult(status=429, body=STATUS_EMPTY)
    if MOCK_SESSION_CONFIG["api_used"].get(api_key, 0) >= MOCK_SESSION_CONFIG["api_limit"]:
        return CallbackResult(status=429, payload=STATUS_429_OVER)
    if MOCK_SESSION_CONFIG[MOCK_BUSY_UNEXPECTED]:
        return CallbackResult(status=429, payload=STATUS_429_UNEXPECTED)
    if MOCK_SESSION_CONFIG[MOCK_OVER_LIMIT]:
        return CallbackResult(status=429, payload=STATUS_429_OVER)
    if MOCK_SESSION_CONFIG[MOCK_BAD_REQUEST]:
        return CallbackResult(status=400, body=STATUS_EMPTY)
    if API_KEY_SITES.get(api_key) is None:
        return CallbackResult(status=403, payload=STATUS_403)
    if MOCK_SESSION_CONFIG[MOCK_FORBIDDEN]:
        return CallbackResult(status=403, payload=STATUS_403)
    if MOCK_SESSION_CONFIG[MOCK_NOT_FOUND]:
        return CallbackResult(status=404, body=STATUS_EMPTY)
    return None


async def _get_sites(url: str, **kwargs: Any) -> CallbackResult:
    try:
        params: dict[str, Any] | None = kwargs.get("params")
        if params is not None:
            api_key = params["api_key"]
            if (abend := _check_abend(api_key)) is not None:
                return abend
            if MOCK_SESSION_CONFIG[MOCK_CORRUPT_SITES]:
                return CallbackResult(body="Not available, a string response")
            return CallbackResult(payload=simulated.raw_get_sites(api_key))
        return CallbackResult(status=500, body="No params found")
    except Exception as e:  # noqa: BLE001
        _LOGGER.error("Error building sites: %s", e)
        return CallbackResult(status=500, body=str(e))


async def _get_solcast(url: str, get: Any, **kwargs: Any) -> CallbackResult:
    try:
        params: dict[str, Any] | None = kwargs.get("params")
        site = str(url).split("_sites/")[1].split("/")[0]
        if params is not None:
            api_key = params["api_key"]
            hours = params.get("hours", 168)
            if (abend := _check_abend(api_key, site=site)) is not None:
                return abend
            MOCK_SESSION_CONFIG["api_used"][api_key] += 1
            return CallbackResult(payload=get(site, api_key, hours))
        return CallbackResult(status=500, body="No params found")
    except Exception as e:  # noqa: BLE001
        _LOGGER.error("Error building past actual data: %s", e)
        return CallbackResult(status=500, body=str(e))


async def _get_forecasts(url: str, **kwargs: Any) -> CallbackResult:
    if MOCK_SESSION_CONFIG[MOCK_CORRUPT_FORECAST]:
        return CallbackResult(body="Not available, a string response")
    kwargs["params"]["hours"] -= 12  # Intentionally return less hours for testing.
    return await _get_solcast(url, simulated.raw_get_site_forecasts, **kwargs)


async def _get_actuals(url: str, **kwargs: Any) -> CallbackResult:
    if MOCK_SESSION_CONFIG[MOCK_CORRUPT_ACTUALS]:
        return CallbackResult(body="Not available, a string response")
    return await _get_solcast(url, simulated.raw_get_site_estimated_actuals, **kwargs)


def session_reset_usage() -> None:
    """Reset the mock session config."""
    MOCK_SESSION_CONFIG["api_used"] = {api_key: 0 for api_key in DEFAULT_INPUT2[CONF_API_KEY].split(",")}


def session_set(setting: str, **kwargs: Any) -> None:
    """Set mock session behaviour."""
    if setting == MOCK_BUSY_SITE:
        MOCK_SESSION_CONFIG[setting] = kwargs.get("site")
        return
    MOCK_SESSION_CONFIG[setting] = True if kwargs.get(MOCK_EXCEPTION) is None else kwargs.get(MOCK_EXCEPTION)


def session_clear(setting: str) -> None:
    """Clear mock session behaviour."""
    match setting:
        case "exception":
            MOCK_SESSION_CONFIG[setting] = None
        case "return_429_for_site":
            MOCK_SESSION_CONFIG[setting] = None
        case _:
            MOCK_SESSION_CONFIG[setting] = False


def aioresponses_reset() -> None:
    """Reset the mock session."""
    session_reset_usage()
    if MOCK_SESSION_CONFIG["aioresponses"] is not None:
        MOCK_SESSION_CONFIG["aioresponses"].stop()
        MOCK_SESSION_CONFIG["aioresponses"] = None


def aioresponses_change_url(url: URL | str | Pattern[Any], new_url: URL | str | Pattern[Any]) -> None:
    """Change URL for the mock session."""
    _LOGGER.critical(MOCK_SESSION_CONFIG["aioresponses"]._matches)
    MOCK_SESSION_CONFIG["aioresponses"].change_url(url, new_url)
    _LOGGER.critical(MOCK_SESSION_CONFIG["aioresponses"]._matches)


async def async_setup_aioresponses() -> None:
    """Set up the mock session."""

    aioresponses_reset()
    aioresp = None
    aioresp = aioresponses(passthrough=["http://127.0.0.1"])

    URLS: dict[str, dict[str, Any]] = {
        "sites": {"URL": r"https://api\.solcast\.com\.au/rooftop_sites\?.*api_key=.*$", "callback": _get_sites},
        "forecasts": {"URL": r"https://api\.solcast\.com\.au/rooftop_sites/.+/forecasts.*$", "callback": _get_forecasts},
        "estimated_actuals": {"URL": r"https://api\.solcast\.com\.au/rooftop_sites/.+/estimated_actuals.*$", "callback": _get_actuals},
    }

    exc = MOCK_SESSION_CONFIG["exception"]
    if exc == ClientConnectionError:
        # Modify the URLs to cause a connection error.
        for url in URLS.values():
            url["URL"] = url["URL"].replace("solcast", "solcastxxxx")
        exc = None

    # Set up the mock GET responses.
    aioresp.get("https://api.solcast.com.au", status=200)
    for _get in URLS.values():
        aioresp.get(re.compile(_get["URL"]), status=200, callback=_get["callback"], repeat=99999, exception=exc)

    MOCK_SESSION_CONFIG["aioresponses"] = aioresp


async def async_init_integration(
    hass: HomeAssistant, options: dict[str, Any], version: int = CONFIG_VERSION, mock_api: bool = True, timezone: str = ZONE_RAW
) -> MockConfigEntry:
    """Set up the Solcast Solar integration in HomeAssistant."""

    session_reset_usage()

    ZONE = ZoneInfo(timezone)
    simulated.set_time_zone(ZONE)

    hass.config.time_zone = timezone
    const.SENSOR_UPDATE_LOGGING = True
    # solcastapi.SENSOR_DEBUG_LOGGING = True

    if options.get(AUTO_UPDATE) is not None:
        options = copy.deepcopy(options)
        options[AUTO_UPDATE] = int(options[AUTO_UPDATE])
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id="solcast_pv_solar", title="Solcast PV Forecast", data=options, options=options, version=version
    )

    entry.add_to_hass(hass)

    if mock_api:
        await async_setup_aioresponses()

    # Ensure that a potentially orphaned simple hard limit diagnostic entity is always present.
    entity_registry = er.async_get(hass)
    entity_registry.async_get_or_create("sensor", DOMAIN, unique_id="solcast_pv_forecast_hard_limit_set", config_entry=entry)

    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    return entry


async def async_cleanup_integration_caches(hass: HomeAssistant, **kwargs: Any) -> bool:
    """Clean up the Solcast Solar integration caches and session."""

    config_dir = hass.config.config_dir

    def list_files() -> list[str]:
        return [str(cache) for cache in Path(config_dir).glob("solcast*.json")]

    try:
        caches = await hass.async_add_executor_job(list_files)
        for cache in caches:
            if not kwargs.get("solcast_dampening", True) and "solcast-dampening" in cache:
                continue
            if not kwargs.get("solcast_sites", True) and "solcast-sites" in cache:
                continue
            _LOGGER.debug("Removing cache file: %s", cache)
            Path(cache).unlink()
    except Exception as e:  # noqa: BLE001
        _LOGGER.error("Error cleaning up Solcast Solar caches: %s", e)
        return False
    return True


async def async_cleanup_integration_tests(hass: HomeAssistant, **kwargs: Any) -> bool:
    """Clean up the Solcast Solar integration caches and session."""

    config_dir = hass.config.config_dir

    def list_files() -> list[str]:
        return [str(cache) for cache in Path(config_dir).glob("solcast*.json")]

    try:
        aioresponses_reset()

        caches = await hass.async_add_executor_job(list_files)
        for cache in caches:
            if not kwargs.get("solcast_dampening", True) and "solcast-dampening" in cache:
                continue
            if not kwargs.get("solcast_sites", True) and "solcast-sites" in cache:
                continue
            _LOGGER.debug("Removing cache file: %s", cache)
            Path(cache).unlink()
    except Exception as e:  # noqa: BLE001
        _LOGGER.error("Error cleaning up Solcast Solar caches: %s", e)
        return False
    return True
