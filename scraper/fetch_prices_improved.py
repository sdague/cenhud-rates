#!/usr/bin/env python3
"""
Improved scraper script to fetch Central Hudson electricity prices.
Supports multiple strategies for extracting data from the website.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup


class CentralHudsonScraper:
    """Scraper for Central Hudson electricity prices."""

    def __init__(self):
        self.url = "https://www.cenhud.com/en/account-resources/rates/gas--electric-supply-prices/"
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
            }
        )

    def extract_price(self, text):
        """Extract numeric price from text string.

        Handles formats like:
        - $0.12345
        - 12.345¢
        - 0.12345
        """
        if not text:
            return None

        # Remove common non-numeric characters
        cleaned = text.strip().replace("$", "").replace("¢", "").replace(",", "")

        # Try to find a decimal number
        match = re.search(r"(\d+\.?\d*)", cleaned)
        if match:
            try:
                value = float(match.group(1))
                # If original had ¢, convert cents to dollars
                if "¢" in text:
                    value = value / 100
                return round(value, 5)
            except ValueError:
                return None
        return None

    def strategy_1_tables(self, soup):
        """Strategy 1: Extract from HTML tables."""
        print("  Trying Strategy 1: HTML tables...")
        rates = {}

        tables = soup.find_all("table")
        print(f"  Found {len(tables)} tables")

        for table_idx, table in enumerate(tables):
            print(f"  Analyzing table {table_idx + 1}...")
            rows = table.find_all("tr")

            for row in rows:
                cells = row.find_all(["td", "th"])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value_text = cells[1].get_text(strip=True)
                    price = self.extract_price(value_text)

                    if price:
                        print(f"    Found: {label} = {price}")
                        # Categorize the rate
                        if any(
                            kw in label
                            for kw in ["residential", "standard", "service class 1"]
                        ):
                            if "kwh" in label or "per kwh" in label:
                                rates["residential_per_kwh"] = price
                        elif "commercial" in label or "service class" in label:
                            if "kwh" in label:
                                rates["commercial_per_kwh"] = price
                        elif "on-peak" in label or "on peak" in label:
                            if "kwh" in label:
                                rates["on_peak_per_kwh"] = price
                        elif "off-peak" in label or "off peak" in label:
                            if "kwh" in label:
                                rates["off_peak_per_kwh"] = price

        return rates if rates else None

    def strategy_2_divs(self, soup):
        """Strategy 2: Extract from div elements with specific classes."""
        print("  Trying Strategy 2: Div elements...")
        rates = {}

        # Look for common price container patterns
        price_containers = soup.find_all(
            ["div", "span", "p"],
            class_=re.compile(r"price|rate|cost|charge", re.I),
        )

        print(f"  Found {len(price_containers)} potential price containers")

        for container in price_containers:
            text = container.get_text(strip=True)
            price = self.extract_price(text)
            if price:
                print(f"    Found price: {price} in: {text[:50]}...")
                # Try to determine rate type from surrounding context
                parent_text = container.parent.get_text(strip=True).lower()
                if "residential" in parent_text or "standard" in parent_text:
                    rates["residential_per_kwh"] = price
                elif "commercial" in parent_text:
                    rates["commercial_per_kwh"] = price

        return rates if rates else None

    def strategy_3_text_search(self, soup):
        """Strategy 3: Search all text for price patterns."""
        print("  Trying Strategy 3: Text pattern search...")
        rates = {}

        # Get all text from the page
        text = soup.get_text()

        # Look for patterns like "Residential: $0.12345/kWh"
        patterns = [
            (r"residential[:\s]+\$?([\d.]+)\s*[¢/]*\s*kwh", "residential_per_kwh"),
            (r"commercial[:\s]+\$?([\d.]+)\s*[¢/]*\s*kwh", "commercial_per_kwh"),
            (r"on[- ]peak[:\s]+\$?([\d.]+)\s*[¢/]*\s*kwh", "on_peak_per_kwh"),
            (r"off[- ]peak[:\s]+\$?([\d.]+)\s*[¢/]*\s*kwh", "off_peak_per_kwh"),
        ]

        for pattern, rate_key in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                price = self.extract_price(match.group(1))
                if price:
                    print(f"    Found {rate_key}: {price}")
                    rates[rate_key] = price
                    break  # Use first match for each type

        return rates if rates else None

    def strategy_4_api_check(self):
        """Strategy 4: Check for JSON/API endpoints."""
        print("  Trying Strategy 4: API endpoints...")

        # Common API endpoint patterns
        api_urls = [
            "https://www.cenhud.com/api/rates/electric",
            "https://www.cenhud.com/api/prices",
            "https://www.cenhud.com/en/api/rates",
        ]

        for api_url in api_urls:
            try:
                response = self.session.get(api_url, timeout=10)
                if response.status_code == 200:
                    try:
                        data = response.json()
                        print(f"    Found API data at {api_url}")
                        return self.parse_api_data(data)
                    except json.JSONDecodeError:
                        continue
            except requests.RequestException:
                continue

        return None

    def parse_api_data(self, data):
        """Parse data from API response."""
        rates = {}
        # This would need to be customized based on actual API structure
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (int, float)):
                    rates[key] = value
        return rates if rates else None

    def fetch_prices(self):
        """Fetch electricity prices using multiple strategies."""
        print(f"Fetching from: {self.url}")

        try:
            response = self.session.get(self.url, timeout=30)
            response.raise_for_status()
            print(f"✓ Page loaded successfully ({len(response.content)} bytes)")

            soup = BeautifulSoup(response.content, "html.parser")

            # Try each strategy in order
            strategies = [
                self.strategy_1_tables,
                self.strategy_2_divs,
                self.strategy_3_text_search,
                self.strategy_4_api_check,
            ]

            for strategy in strategies:
                try:
                    if strategy == self.strategy_4_api_check:
                        rates = strategy()
                    else:
                        rates = strategy(soup)

                    if rates:
                        print(
                            f"✓ Successfully extracted rates using {strategy.__name__}"
                        )
                        return self.format_rates(rates)
                except Exception as e:
                    print(f"  Strategy failed: {e}")
                    continue

            print("✗ All strategies failed to extract rates")
            return None

        except requests.RequestException as e:
            print(f"✗ Error fetching page: {e}")
            return None

    def format_rates(self, raw_rates):
        """Format extracted rates into standard structure."""
        formatted = {
            "effective_date": datetime.now().strftime("%Y-%m-%d"),
            "last_updated": datetime.now().isoformat(),
            "standard": {},
            "time_of_use": {"on_peak": {}, "off_peak": {}},
        }

        # Map extracted rates to standard structure
        if "residential_per_kwh" in raw_rates:
            formatted["standard"]["total_per_kwh"] = raw_rates["residential_per_kwh"]

        if "commercial_per_kwh" in raw_rates:
            formatted["commercial"] = {"total_per_kwh": raw_rates["commercial_per_kwh"]}

        if "on_peak_per_kwh" in raw_rates:
            formatted["time_of_use"]["on_peak"]["total_per_kwh"] = raw_rates[
                "on_peak_per_kwh"
            ]

        if "off_peak_per_kwh" in raw_rates:
            formatted["time_of_use"]["off_peak"]["total_per_kwh"] = raw_rates[
                "off_peak_per_kwh"
            ]

        return formatted


def save_prices(
    new_rate, output_file="../custom_components/central_hudson/data/prices.json"
):
    """Save prices to JSON file."""
    if not new_rate:
        return False

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing data
    if output_path.exists():
        with open(output_path) as f:
            data = json.load(f)
    else:
        data = {"customer_charge": 22.50, "rates": []}

    # Check if rate already exists
    effective_date = new_rate.get("effective_date")
    existing_dates = [r.get("effective_date") for r in data.get("rates", [])]

    if effective_date in existing_dates:
        print(f"\nUpdating existing rate for {effective_date}")
        for i, rate in enumerate(data["rates"]):
            if rate.get("effective_date") == effective_date:
                data["rates"][i] = new_rate
                break
    else:
        print(f"\nAdding new rate for {effective_date}")
        data["rates"].append(new_rate)

    # Sort by date (most recent first)
    data["rates"].sort(key=lambda x: x.get("effective_date", ""), reverse=True)

    # Save
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Saved to {output_file}")
    print(f"  Total historical rates: {len(data['rates'])}")
    print("\nCurrent rate (most recent):")
    print(json.dumps(data["rates"][0], indent=2))
    return True


def main():
    """Main entry point."""
    print("=" * 60)
    print("Central Hudson Electric Rates Scraper")
    print("=" * 60)
    print()

    scraper = CentralHudsonScraper()
    rates = scraper.fetch_prices()

    if rates:
        print("\n" + "=" * 60)
        print("Extracted Rates:")
        print("=" * 60)
        print(json.dumps(rates, indent=2))
        print()

        if save_prices(rates):
            print("\n✓ Success!")
            return 0
        else:
            print("\n✗ Failed to save rates")
            return 1
    else:
        print("\n" + "=" * 60)
        print("Failed to extract rates")
        print("=" * 60)
        print("\nTroubleshooting:")
        print("1. Check if the website structure has changed")
        print("2. Try running with --debug flag for more details")
        print("3. Manually verify rates at:")
        print("   https://www.cenhud.com/en/account-resources/rates/")
        print("4. You can manually update prices.json if needed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
