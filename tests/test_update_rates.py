"""Tests for scripts/update_rates.py."""

import importlib.util
import json
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "update_rates", ROOT / "scripts" / "update_rates.py"
)
ur = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ur)

PRICES = json.loads(
    (ROOT / "custom_components/central_hudson/data/prices.json").read_text()
)
HISTORY = (ROOT / "RATE_HISTORY.md").read_text()

SUPPLY = {"standard": 0.09, "on_peak": 0.12, "off_peak": 0.06}
DELIVERY = {"standard": 0.14554, "on_peak": 0.15516, "off_peak": 0.13417}
UPDATED = datetime.combine(
    date(2026, 12, 11), time(12, 0), tzinfo=ZoneInfo("America/New_York")
)


def new_rate(eff=date(2026, 12, 11)):
    return ur.build_rate(eff, SUPPLY, DELIVERY, UPDATED)


def test_build_rate_roundtrips_existing_entry():
    """Rebuilding an existing entry from its charges reproduces it exactly."""
    existing = PRICES["rates"][0]
    supply, delivery = ur.rate_charges(existing)
    updated = datetime.fromisoformat(existing["last_updated"])
    rebuilt = ur.build_rate(
        date.fromisoformat(existing["effective_date"]), supply, delivery, updated
    )
    assert rebuilt == existing


def test_build_rate_totals_and_timestamp():
    rate = new_rate()
    assert rate["standard"]["total_per_kwh"] == 0.23554
    assert rate["time_of_use"]["on_peak"]["total_per_kwh"] == 0.27516
    assert rate["last_updated"] == "2026-12-11T12:00:00-05:00"


def test_merge_rate_inserts_sorted_and_replaces():
    merged = ur.merge_rate(PRICES, new_rate(), 23.0)
    assert merged["rates"][0]["effective_date"] == "2026-12-11"
    assert len(merged["rates"]) == len(PRICES["rates"]) + 1
    assert merged["customer_charge"] == 23.0

    again = ur.merge_rate(merged, new_rate(), 23.0)
    assert len(again["rates"]) == len(merged["rates"])

    older = ur.merge_rate(PRICES, new_rate(date(2026, 9, 5)), 22.5)
    dates = [r["effective_date"] for r in older["rates"]]
    assert dates == sorted(dates, reverse=True)


def test_history_section_matches_existing_format():
    existing = PRICES["rates"][0]
    section = ur.history_section(existing, PRICES["customer_charge"])
    assert section in HISTORY


def test_update_history_inserts_newest_first():
    out = ur.update_history(HISTORY, new_rate(), 22.5)
    assert out.index("(Effective: 2026-12-11)") < out.index("(Effective: 2026-11-11)")
    assert out.count("### December 2026") == 1
    # Re-running replaces rather than duplicating.
    again = ur.update_history(out, new_rate(), 22.5)
    assert again == out


def test_update_history_inserts_in_middle_and_oldest():
    mid = ur.update_history(HISTORY, new_rate(date(2026, 9, 5)), 22.5)
    assert mid.index("(Effective: 2026-09-11)") < mid.index("(Effective: 2026-09-05)")
    assert mid.index("(Effective: 2026-09-05)") < mid.index("(Effective: 2026-09-01)")

    oldest = ur.update_history(HISTORY, new_rate(date(2025, 1, 1)), 22.5)
    assert oldest.index("(Effective: 2025-01-01)") < oldest.index("## Notes")
    assert oldest.index("(Effective: 2026-02-11)") < oldest.index(
        "(Effective: 2025-01-01)"
    )


def test_update_history_replaces_existing_section():
    existing = PRICES["rates"][0]
    supply, delivery = ur.rate_charges(existing)
    supply["standard"] = 0.07
    changed = ur.build_rate(
        date.fromisoformat(existing["effective_date"]), supply, delivery, UPDATED
    )
    out = ur.update_history(HISTORY, changed, 22.5)
    assert out.count("(Effective: 2026-11-11)") == 1
    assert "- Standard: $0.07000/kWh" in out
    assert "(Effective: 2026-10-12)" in out


def test_changelog_entry_format():
    assert (
        ur.changelog_entry(date(2026, 11, 11)) == "- Updated with Nov 11, 2026 prices"
    )


CHANGELOG_EMPTY = "# Changelog\n\n## [Unreleased]\n\n## [1.3.9] - 2026-11-17\n\n### Changed\n\n- Old\n"


def test_update_changelog_empty_unreleased():
    out = ur.update_changelog(CHANGELOG_EMPTY, "- New")
    assert out == (
        "# Changelog\n\n## [Unreleased]\n\n### Changed\n\n- New\n\n## [1.3.9] - 2026-11-17\n\n### Changed\n\n- Old\n"
    )


def test_update_changelog_appends_to_existing_changed():
    text = "## [Unreleased]\n\n### Changed\n\n- First\n\n## [1.0.0]\n"
    out = ur.update_changelog(text, "- Second")
    assert out == "## [Unreleased]\n\n### Changed\n\n- First\n- Second\n\n## [1.0.0]\n"
    assert ur.update_changelog(out, "- Second") == out


def test_update_changelog_with_other_section_only():
    text = "## [Unreleased]\n\n### Fixed\n\n- Bug\n\n## [1.0.0]\n"
    out = ur.update_changelog(text, "- New")
    assert (
        out
        == "## [Unreleased]\n\n### Changed\n\n- New\n\n### Fixed\n\n- Bug\n\n## [1.0.0]\n"
    )


@pytest.mark.parametrize(
    "raw,expected", [("0.08086", 0.08086), ("$0.1", 0.1), (" $ 0.05 ", 0.05)]
)
def test_parse_charge_valid(raw, expected):
    assert ur.parse_charge(raw) == expected


@pytest.mark.parametrize("raw", ["8.086", "0", "-0.1", "abc", "0.080864"])
def test_parse_charge_invalid(raw):
    with pytest.raises(ValueError):
        ur.parse_charge(raw)


def test_update_changelog_no_blank_after_heading_or_trailing_newline():
    text = "## [Unreleased]\n\n### Changed\n- First"
    out = ur.update_changelog(text, "- Second")
    assert out == "## [Unreleased]\n\n### Changed\n- First\n- Second\n"


def test_update_changelog_missing_unreleased():
    with pytest.raises(ValueError):
        ur.update_changelog("# Changelog\n\n## [1.0.0]\n", "- New")


def test_update_history_replace_without_rule_keeps_next_section():
    text = (
        "## Rate History\n\n"
        "### December 2026 (Effective: 2026-12-11)\n\nold\n\n"
        "### November 2026 (Effective: 2026-11-11)\n\nnov\n\n---\n\n"
        "## Notes\n"
    )
    out = ur.update_history(text, new_rate(), 22.5)
    assert "old" not in out
    assert "### November 2026 (Effective: 2026-11-11)\n\nnov\n\n---\n" in out


def test_update_history_replaces_even_when_unsorted():
    text = (
        "## Rate History\n\n"
        "### November 2026 (Effective: 2026-11-11)\n\nnov\n\n---\n\n"
        "### December 2026 (Effective: 2026-12-11)\n\nold\n\n---\n\n"
    )
    out = ur.update_history(text, new_rate(), 22.5)
    assert out.count("(Effective: 2026-12-11)") == 1
    assert "old" not in out


def test_write_atomic(tmp_path):
    a, b = tmp_path / "a.txt", tmp_path / "b.txt"
    a.write_text("old")
    ur.write_atomic({a: "new a", b: "new b"})
    assert a.read_text() == "new a"
    assert b.read_text() == "new b"
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.txt", "b.txt"]
