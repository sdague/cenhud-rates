#!/usr/bin/env python3
"""
Scraper script to fetch Central Hudson electricity prices.
Run this monthly to update the prices data file.
"""

import json
import sys
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def fetch_prices():
    """Fetch electricity prices from Central Hudson website."""
    url = (
        "https://www.cenhud.com/en/account-resources/rates/gas--electric-supply-prices/"
    )

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, "html.parser")

        # Extract price data from the page
        # This will need to be adjusted based on the actual HTML structure
        new_rate = {
            "effective_date": datetime.now().strftime("%Y-%m-%d"),
            "last_updated": datetime.now().isoformat(),
            "standard": {},
            "time_of_use": {"on_peak": {}, "off_peak": {}},
        }

        # Look for price tables or specific elements
        # Example structure - adjust based on actual page:
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")
            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)

                    # Try to extract numeric price
                    try:
                        # Remove $ and convert to float
                        price_value = float(
                            value.replace("$", "").replace("¢", "").strip()
                        )

                        # Parse different rate types
                        if "standard" in label and "kwh" in label:
                            new_rate["standard"]["total_per_kwh"] = price_value
                        elif "on-peak" in label or "on peak" in label:
                            if "kwh" in label:
                                new_rate["time_of_use"]["on_peak"]["total_per_kwh"] = (
                                    price_value
                                )
                        elif "off-peak" in label or "off peak" in label:
                            if "kwh" in label:
                                new_rate["time_of_use"]["off_peak"]["total_per_kwh"] = (
                                    price_value
                                )
                    except ValueError:
                        continue

        return new_rate

    except requests.RequestException as e:
        print(f"Error fetching prices: {e}", file=sys.stderr)
        return None


def save_prices(
    new_rate, output_file="../custom_components/central_hudson/data/prices.json"
):
    """Save prices to JSON file, appending to historical data."""
    if not new_rate:
        return False

    import os

    # Load existing data if file exists
    if os.path.exists(output_file):
        with open(output_file) as f:
            data = json.load(f)
    else:
        data = {"customer_charge": 22.50, "rates": []}

    # Check if this effective date already exists
    effective_date = new_rate.get("effective_date")
    existing_dates = [r.get("effective_date") for r in data.get("rates", [])]

    if effective_date in existing_dates:
        print(f"Rate for {effective_date} already exists. Updating...")
        # Update existing rate
        for i, rate in enumerate(data["rates"]):
            if rate.get("effective_date") == effective_date:
                data["rates"][i] = new_rate
                break
    else:
        print(f"Adding new rate for {effective_date}")
        # Append new rate
        data["rates"].append(new_rate)

    # Sort rates by effective_date (most recent first)
    data["rates"].sort(key=lambda x: x.get("effective_date", ""), reverse=True)

    # Save updated data
    with open(output_file, "w") as f:
        json.dump(data, f, indent=2)

    print(f"Prices saved to {output_file}")
    print(f"Total historical rates: {len(data['rates'])}")
    print("Current rate (most recent):")
    print(json.dumps(data["rates"][0], indent=2))
    return True


if __name__ == "__main__":
    print("Fetching Central Hudson electricity prices...")
    new_rate = fetch_prices()

    if new_rate:
        save_prices(new_rate)
        sys.exit(0)
    else:
        print(
            "Failed to fetch prices. Please check the website manually.",
            file=sys.stderr,
        )
        print("You can manually add rates to the prices.json file.", file=sys.stderr)
        sys.exit(1)
