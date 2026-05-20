"""Unit tests for issues.py."""

from homeassistant.components.solcast_solar.const import (
    ISSUE_UNUSUAL_AZIMUTH_NORTHERN,
    ISSUE_UNUSUAL_AZIMUTH_SOUTHERN,
)
from homeassistant.components.solcast_solar.issues import check_unusual_azimuth


class TestCheckUnusualAzimuth:
    """Tests for check_unusual_azimuth."""

    def test_northern_facing_south_is_not_unusual(self) -> None:
        """A north-hemisphere site facing south (180°) is a normal orientation."""
        unusual, _, _ = check_unusual_azimuth(51.5, 180)
        assert not unusual, "North-hemisphere site facing 180° (south) should not be flagged as unusual"

    def test_northern_facing_north_positive_is_unusual(self) -> None:
        """A north-hemisphere site facing northeast (45°) should be flagged as unusual."""
        unusual, issue_key, _ = check_unusual_azimuth(51.5, 45)
        assert unusual, "North-hemisphere site facing 45° (northeast) should be flagged as unusual"
        assert issue_key == ISSUE_UNUSUAL_AZIMUTH_NORTHERN, f"Expected northern issue key, got {issue_key!r}"

    def test_southern_facing_north_is_not_unusual(self) -> None:
        """A south-hemisphere site facing north (0°) is a normal orientation."""
        unusual, _, _ = check_unusual_azimuth(-33.9, 0)
        assert not unusual, "South-hemisphere site facing 0° (north) should not be flagged as unusual"

    def test_southern_facing_south_is_unusual(self) -> None:
        """A south-hemisphere site facing south (160°) should be flagged as unusual."""
        unusual, issue_key, _ = check_unusual_azimuth(-33.9, 160)
        assert unusual, "South-hemisphere site facing 160° (south) should be flagged as unusual"
        assert issue_key == ISSUE_UNUSUAL_AZIMUTH_SOUTHERN, f"Expected southern issue key, got {issue_key!r}"

    def test_northern_negative_azimuth_valid(self) -> None:
        """A north-hemisphere site with a westerly negative azimuth (-135°) is a normal orientation."""
        unusual, _, _ = check_unusual_azimuth(51.5, -135)
        assert not unusual, "North-hemisphere site facing -135° (southwest) should not be flagged as unusual"

    def test_northern_negative_azimuth_invalid(self) -> None:
        """A north-hemisphere site with a northerly negative azimuth (-45°) should be flagged."""
        unusual, issue_key, _ = check_unusual_azimuth(51.5, -45)
        assert unusual, "North-hemisphere site facing -45° (northwest) should be flagged as unusual"
        assert issue_key == ISSUE_UNUSUAL_AZIMUTH_NORTHERN, f"Expected northern issue key, got {issue_key!r}"
