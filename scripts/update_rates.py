#!/usr/bin/env python3
"""Interactively add a new Central Hudson rate period to the repo.

Prompts for the effective date and per-kWh charges, then updates:

- custom_components/central_hudson/data/prices.json
- RATE_HISTORY.md
- CHANGELOG.md (under [Unreleased])

Delivery charges and the customer charge default to the most recent
values, since they rarely change month to month. Press Enter to accept a
default.

Usage: python scripts/update_rates.py
"""

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
from datetime import date, datetime, time
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent
PRICES_FILE = (
    REPO_ROOT / "custom_components" / "central_hudson" / "data" / "prices.json"
)
HISTORY_FILE = REPO_ROOT / "RATE_HISTORY.md"
CHANGELOG_FILE = REPO_ROOT / "CHANGELOG.md"

TZ = ZoneInfo("America/New_York")

DESCRIPTIONS = {
    "standard": "Standard residential rate (supply + delivery)",
    "on_peak": "Time-of-Use on-peak rate (supply + delivery)",
    "off_peak": "Time-of-Use off-peak rate (supply + delivery)",
}

LABELS = {"standard": "Standard", "on_peak": "On-Peak", "off_peak": "Off-Peak"}

HEADING_RE = re.compile(r"^### .+ \(Effective: (\d{4}-\d{2}-\d{2})\)$", re.M)


# ---------------------------------------------------------------------------
# Pure helpers (tested)
# ---------------------------------------------------------------------------


def build_rate(
    effective_date: date,
    supply: dict[str, float],
    delivery: dict[str, float],
    updated: datetime,
) -> dict:
    """Build a rate entry in the prices.json format."""

    def block(key: str) -> dict:
        return {
            "supply_charge": supply[key],
            "delivery_charge": delivery[key],
            "total_per_kwh": round(supply[key] + delivery[key], 5),
            "description": DESCRIPTIONS[key],
        }

    return {
        "effective_date": effective_date.isoformat(),
        "last_updated": updated.isoformat(),
        "standard": block("standard"),
        "time_of_use": {"on_peak": block("on_peak"), "off_peak": block("off_peak")},
    }


def rate_charges(rate: dict) -> tuple[dict[str, float], dict[str, float]]:
    """Return (supply, delivery) dicts keyed by standard/on_peak/off_peak."""
    blocks = {
        "standard": rate["standard"],
        "on_peak": rate["time_of_use"]["on_peak"],
        "off_peak": rate["time_of_use"]["off_peak"],
    }
    supply = {k: v["supply_charge"] for k, v in blocks.items()}
    delivery = {k: v["delivery_charge"] for k, v in blocks.items()}
    return supply, delivery


def merge_rate(data: dict, new_rate: dict, customer_charge: float) -> dict:
    """Insert or replace new_rate in data, keeping rates sorted newest first."""
    rates = [
        r
        for r in data.get("rates", [])
        if r["effective_date"] != new_rate["effective_date"]
    ]
    rates.append(new_rate)
    rates.sort(key=lambda r: r["effective_date"], reverse=True)
    return {**data, "customer_charge": customer_charge, "rates": rates}


def history_section(rate: dict, customer_charge: float) -> str:
    """Render a RATE_HISTORY.md section for a rate entry."""
    eff = date.fromisoformat(rate["effective_date"])
    supply, delivery = rate_charges(rate)
    keys = ("standard", "on_peak", "off_peak")

    def lines(values: dict[str, float]) -> str:
        return "\n".join(f"- {LABELS[k]}: ${values[k]:.5f}/kWh" for k in keys)

    totals = {k: round(supply[k] + delivery[k], 5) for k in keys}
    return (
        f"### {eff.strftime('%B %Y')} (Effective: {eff.isoformat()})\n\n"
        f"**Supply Charges:**\n{lines(supply)}\n\n"
        f"**Delivery Charges:**\n{lines(delivery)}\n\n"
        f"**Total Rates (Supply + Delivery):**\n{lines(totals)}\n\n"
        f"**Customer Charge:** ${customer_charge:.2f}/month\n\n"
        "---\n\n"
    )


def update_history(text: str, rate: dict, customer_charge: float) -> str:
    """Insert (or replace) the section for rate, keeping newest first."""
    eff = rate["effective_date"]
    section = history_section(rate, customer_charge)

    for m in HEADING_RE.finditer(text):
        if m.group(1) == eff:
            # The section ends at its "---" rule, but never past the next heading.
            nxt = re.compile(r"^##", re.M).search(text, m.end())
            limit = nxt.start() if nxt else len(text)
            rule = text.find("---\n", m.end(), limit)
            end = rule + len("---\n") if rule != -1 else limit
            while text[end : end + 1] == "\n":
                end += 1
            return text[: m.start()] + section + text[end:]

    for m in HEADING_RE.finditer(text):
        if m.group(1) < eff:
            return text[: m.start()] + section + text[m.start() :]

    # Older than everything (or no entries yet): place before "## Notes".
    notes = text.find("\n## Notes")
    if notes != -1:
        return text[: notes + 1] + section + text[notes + 1 :]
    if "## Rate History" not in text:
        raise ValueError("Could not find '## Rate History' heading in RATE_HISTORY.md")
    return text.rstrip("\n") + "\n\n" + section


def changelog_entry(effective_date: date) -> str:
    return f"- Updated with {effective_date.strftime('%b')} {effective_date.day}, {effective_date.year} prices"


def update_changelog(text: str, entry: str) -> str:
    """Add entry under '### Changed' in the [Unreleased] section."""
    m = re.search(r"^## \[Unreleased\][^\n]*\n", text, re.M)
    if not m:
        raise ValueError("Could not find '## [Unreleased]' in CHANGELOG.md")
    start = m.end()
    nxt = re.search(r"^## \[", text[start:], re.M)
    end = start + nxt.start() if nxt else len(text)
    body = text[start:end]

    if entry in body:
        return text

    if not body.endswith("\n"):
        body += "\n"
    changed = re.search(r"^### Changed[ \t]*\n\n?", body, re.M)
    if changed:
        # Append after the last bullet of the existing Changed list.
        after = body[changed.end() :]
        bullets = re.match(r"(?:- [^\n]*\n(?:  [^\n]*\n)*)*", after)
        pos = changed.end() + bullets.end()
        new_body = body[:pos] + entry + "\n" + body[pos:]
    else:
        new_body = "\n### Changed\n\n" + entry + "\n\n" + body.lstrip("\n")
    return text[:start] + new_body + text[end:]


def parse_charge(raw: str, max_value: float = 1.0) -> float:
    """Parse a $/kWh value like '0.08086' or '$0.08086'."""
    value = float(raw.strip().lstrip("$").strip())
    if not 0 < value < max_value:
        raise ValueError(f"value must be between 0 and {max_value}")
    if round(value, 5) != value:
        raise ValueError("use at most 5 decimal places")
    return value


# ---------------------------------------------------------------------------
# Interactive prompts
# ---------------------------------------------------------------------------


def ask(prompt: str, default: str | None = None) -> str:
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt}{suffix}: ").strip()
        if raw:
            return raw
        if default is not None:
            return default


def ask_date(prompt: str, default: date) -> date:
    while True:
        raw = ask(prompt, default.isoformat())
        try:
            return date.fromisoformat(raw)
        except ValueError:
            print("  Please enter a date as YYYY-MM-DD.")


def ask_charge(
    prompt: str, default: float | None = None, max_value: float = 1.0
) -> float:
    while True:
        raw = ask(prompt, None if default is None else f"{default}")
        try:
            return parse_charge(raw, max_value)
        except ValueError as err:
            print(f"  Invalid value ({err}). Enter dollars, e.g. 0.08086.")


def confirm(prompt: str) -> bool:
    return input(f"{prompt} [y/N]: ").strip().lower() in ("y", "yes")


def write_atomic(files: dict[Path, str]) -> None:
    """Write all files via temp files, then rename them into place together.

    Every temp file is fully written before any original is replaced, so a
    failure while writing leaves the repo untouched.
    """
    temps: dict[Path, Path] = {}
    try:
        for path, content in files.items():
            fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
            with os.fdopen(fd, "w") as f:
                f.write(content)
            temps[path] = Path(tmp)
        for path, tmp in temps.items():
            os.replace(tmp, path)
    finally:
        for tmp in temps.values():
            tmp.unlink(missing_ok=True)


def main() -> int:
    data = json.loads(PRICES_FILE.read_text())
    rates = data.get("rates", [])
    latest = max(rates, key=lambda r: r["effective_date"]) if rates else None
    prev_supply, prev_delivery = rate_charges(latest) if latest else ({}, {})

    print("Central Hudson rate update")
    if latest:
        print(f"Most recent rate in repo: effective {latest['effective_date']}")
    print("Enter charges in $/kWh. Press Enter to accept [defaults].\n")

    eff = ask_date("Effective date (YYYY-MM-DD)", date.today())
    existing = next(
        (r for r in data.get("rates", []) if r["effective_date"] == eff.isoformat()),
        None,
    )
    if existing:
        print(f"  Note: a rate for {eff} already exists and will be replaced.")
        prev_supply, prev_delivery = rate_charges(existing)

    print("\nSupply charges:")
    supply = {
        k: ask_charge(f"  {LABELS[k]} supply", prev_supply.get(k) if existing else None)
        for k in LABELS
    }

    print("\nDelivery charges:")
    delivery = {
        k: ask_charge(f"  {LABELS[k]} delivery", prev_delivery.get(k)) for k in LABELS
    }

    customer_charge = ask_charge(
        "\nCustomer charge ($/month)", data.get("customer_charge"), max_value=1000
    )

    updated = datetime.combine(date.today(), time(12, 0), tzinfo=TZ)
    new_rate = build_rate(eff, supply, delivery, updated)

    print("\n" + history_section(new_rate, customer_charge).rstrip("-\n"))
    if customer_charge != data.get("customer_charge"):
        print(
            f"WARNING: customer charge changes from {data.get('customer_charge')} to "
            f"{customer_charge}. It is a single global value and takes effect "
            "immediately, not on the effective date.\n"
        )
    if latest and not existing and eff.isoformat() > latest["effective_date"]:
        print("Change in total vs previous period:")
        for k in LABELS:
            old = round(prev_supply[k] + prev_delivery[k], 5)
            new = round(supply[k] + delivery[k], 5)
            print(f"  {LABELS[k]}: ${old:.5f} -> ${new:.5f} ({new - old:+.5f})")
        print()

    if not confirm("Write these rates to the repo?"):
        print("Aborted; no files changed.")
        return 1

    # Compute every new file before touching any of them.
    try:
        contents = {
            PRICES_FILE: json.dumps(
                merge_rate(data, new_rate, customer_charge), indent=2
            )
            + "\n",
            HISTORY_FILE: update_history(
                HISTORY_FILE.read_text(), new_rate, customer_charge
            ),
            CHANGELOG_FILE: update_changelog(
                CHANGELOG_FILE.read_text(), changelog_entry(eff)
            ),
        }
    except ValueError as err:
        print(f"Error: {err}\nNo files changed.")
        return 1
    write_atomic(contents)

    for path in (PRICES_FILE, HISTORY_FILE, CHANGELOG_FILE):
        print(f"Updated {path.relative_to(REPO_ROOT)}")
    print("\nNext: review with `git diff`, run `make lint test`, and commit.")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyboardInterrupt, EOFError):
        print("\nAborted; no files changed.")
        sys.exit(1)
