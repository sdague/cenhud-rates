#!/usr/bin/env python3
"""
Advanced scraper using Selenium for JavaScript-rendered content.
Use this if the standard scraper fails due to dynamic content.

Requirements:
    pip install selenium webdriver-manager
"""

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager
except ImportError:
    print("Error: Selenium not installed")
    print("Install with: pip install selenium webdriver-manager")
    sys.exit(1)


class SeleniumScraper:
    """Scraper using Selenium for JavaScript-rendered pages."""

    def __init__(self, headless=True):
        self.url = "https://www.cenhud.com/en/account-resources/rates/gas--electric-supply-prices/"
        self.headless = headless
        self.driver = None

    def setup_driver(self):
        """Set up Chrome driver with appropriate options."""
        print("Setting up Chrome driver...")
        options = Options()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.implicitly_wait(10)

    def extract_price(self, text):
        """Extract numeric price from text."""
        if not text:
            return None

        cleaned = text.strip().replace("$", "").replace("¢", "").replace(",", "")
        match = re.search(r"(\d+\.?\d*)", cleaned)

        if match:
            try:
                value = float(match.group(1))
                if "¢" in text:
                    value = value / 100
                return round(value, 5)
            except ValueError:
                return None
        return None

    def wait_for_content(self):
        """Wait for page content to load."""
        print("Waiting for page to load...")
        try:
            # Wait for Electric tab to be present
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, "//*[contains(text(), 'Electric')]")
                )
            )
            print("✓ Page loaded")

            # Scroll down to trigger dynamic content loading
            print("Scrolling to load dynamic content...")
            self.driver.execute_script(
                "window.scrollTo(0, document.body.scrollHeight);"
            )
            time.sleep(3)

            # Wait for actual pricing data to appear (look for dollar amounts)
            print("Waiting for pricing data to render...")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[contains(text(), 'Standard Rate') or contains(text(), '$0.')]",
                    )
                )
            )
            print("✓ Pricing data loaded")

            # Give extra time for all data to render
            time.sleep(2)
            return True
        except Exception as e:
            print(f"✗ Timeout waiting for content: {e}")
            import traceback

            traceback.print_exc()
            return False

    def click_electric_tab(self):
        """Click on the Electric tab if it exists."""
        try:
            # Try to find and click Electric tab
            electric_tab = self.driver.find_element(
                By.XPATH,
                "//a[contains(text(), 'Electric')] | //button[contains(text(), 'Electric')]",
            )
            electric_tab.click()
            print("✓ Clicked Electric tab")
            time.sleep(2)  # Wait for content to load
            return True
        except Exception as e:
            print(f"  Could not click Electric tab: {e}")
            return False

    def extract_from_tables(self):
        """Extract prices from HTML tables."""
        print("Extracting from tables...")
        rates = {}

        try:
            # Try to find tables by tag
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"  Found {len(tables)} <table> elements")

            # Also try to find table-like structures by looking for the pricing header
            if not tables:
                print("  No <table> tags found, looking for table-like structures...")
                # Look for elements containing the pricing data
                potential_tables = self.driver.find_elements(
                    By.XPATH,
                    "//*[contains(text(), 'Electric Supply Prices')]/following::*[contains(@class, 'table') or contains(@role, 'table')]",
                )
                if potential_tables:
                    print(f"  Found {len(potential_tables)} potential table structures")
                    tables = potential_tables

            for table_idx, table in enumerate(tables):
                rows = table.find_elements(By.TAG_NAME, "tr")
                print(f"  Analyzing table {table_idx + 1} with {len(rows)} rows")

                # Look for header rows to identify columns
                # The table may have nested headers (Time-of-Use Rates* spans On-Peak and Off-Peak)
                header_row = None

                for row_idx, row in enumerate(rows):
                    try:
                        # Check if this is a header row
                        headers = row.find_elements(By.TAG_NAME, "th")
                        if headers and not header_row:
                            header_row = row_idx
                            for col_idx, header in enumerate(headers):
                                header_text = header.text.strip().lower()
                                print(f"    Header col {col_idx}: {header_text}")
                            continue

                        # Extract data rows
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if not cells:
                            continue

                        # Get the date/label from first column
                        if len(cells) > 0:
                            label = cells[0].text.strip().lower()

                            # Look for rows with actual month names (skip "avg" which is 12-month average)
                            if any(
                                month in label
                                for month in [
                                    "jan",
                                    "feb",
                                    "mar",
                                    "apr",
                                    "may",
                                    "jun",
                                    "jul",
                                    "aug",
                                    "sep",
                                    "oct",
                                    "nov",
                                    "dec",
                                ]
                            ):
                                # Skip if we already found rates (first data row after avg is what we want)
                                if rates:
                                    print(f"    Skipping additional row: {label}")
                                    continue

                                print(f"    Processing row: {label}")
                                print(f"      Row has {len(cells)} cells")

                                # Extract all prices from the row
                                for cell_idx, cell in enumerate(cells):
                                    cell_text = cell.text.strip()
                                    if cell_text and "$" in cell_text:
                                        print(f"      Cell {cell_idx}: {cell_text}")

                                # Try to extract based on column positions
                                # Typically: [Date, Standard, On-Peak, Off-Peak]
                                # These are SUPPLY charges only
                                if len(cells) >= 2:
                                    price = self.extract_price(cells[1].text)
                                    if price:
                                        rates["residential_supply"] = price
                                        print(f"      Standard supply: {price}")

                                if len(cells) >= 3:
                                    price = self.extract_price(cells[2].text)
                                    if price:
                                        rates["on_peak_supply"] = price
                                        print(f"      On-peak supply: {price}")

                                if len(cells) >= 4:
                                    price = self.extract_price(cells[3].text)
                                    if price:
                                        rates["off_peak_supply"] = price
                                        print(f"      Off-peak supply: {price}")

                                # If we found all rates, we can stop
                                if all(
                                    k in rates
                                    for k in [
                                        "residential_supply",
                                        "on_peak_supply",
                                        "off_peak_supply",
                                    ]
                                ):
                                    break

                    except Exception as e:
                        print(f"    Error processing row: {e}")
                        continue

                # If we found rates in this table, stop looking
                if rates:
                    break

        except Exception as e:
            print(f"  Error extracting from tables: {e}")
            import traceback

            traceback.print_exc()

        return rates if rates else None

    def extract_from_page_text(self):
        """Extract prices from all page text."""
        print("Extracting from page text...")
        rates = {}

        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text
            print(f"  Page text length: {len(page_text)} characters")

            # Look for the most recent rates (first data row after headers)
            # Pattern: look for lines with dates followed by prices
            lines = page_text.split("\n")

            found_header = False
            skip_first_data_row = True  # Skip the 12-month average row

            for i, line in enumerate(lines):
                # Look for the header row
                if "standard rate" in line.lower() and (
                    "on-peak" in line.lower() or "on peak" in line.lower()
                ):
                    found_header = True
                    print(f"  Found header at line {i}: {line[:80]}")
                    continue

                # After finding header, look for data rows
                if found_header and i < len(lines) - 1:
                    # Check if this line has a date pattern (month name, skip "avg")
                    if any(
                        month in line.lower()
                        for month in [
                            "jan",
                            "feb",
                            "mar",
                            "apr",
                            "may",
                            "jun",
                            "jul",
                            "aug",
                            "sep",
                            "oct",
                            "nov",
                            "dec",
                        ]
                    ):
                        # Skip the first data row (12-month average)
                        if skip_first_data_row:
                            print(f"  Skipping 12-month average row: {line}")
                            skip_first_data_row = False
                            continue

                        print(f"  Found data row: {line}")
                        # Extract all prices from this line
                        prices = re.findall(r"\$?([\d.]+)", line)
                        if len(prices) >= 3:
                            print(f"    Extracted prices: {prices}")
                            # First price is standard supply, second is on-peak supply, third is off-peak supply
                            if not rates.get("residential_supply"):
                                rates["residential_supply"] = self.extract_price(
                                    prices[0]
                                )
                            if not rates.get("on_peak_supply"):
                                rates["on_peak_supply"] = self.extract_price(prices[1])
                            if not rates.get("off_peak_supply"):
                                rates["off_peak_supply"] = self.extract_price(prices[2])

                            # If we found all rates, we're done
                            if all(
                                k in rates
                                for k in [
                                    "residential_supply",
                                    "on_peak_supply",
                                    "off_peak_supply",
                                ]
                            ):
                                break

        except Exception as e:
            print(f"  Error extracting from text: {e}")
            import traceback

            traceback.print_exc()

        return rates if rates else None

    def fetch_prices(self):
        """Fetch prices using Selenium."""
        try:
            self.setup_driver()
            print(f"\nNavigating to: {self.url}")
            self.driver.get(self.url)

            if not self.wait_for_content():
                return None

            # Try to click Electric tab
            self.click_electric_tab()

            # Take screenshot for debugging
            screenshot_path = Path("scraper_screenshot.png")
            self.driver.save_screenshot(str(screenshot_path))
            print(f"✓ Screenshot saved to {screenshot_path}")

            # Save HTML for debugging
            html_path = Path("scraper_page.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(self.driver.page_source)
            print(f"✓ HTML saved to {html_path}")

            # Try extraction strategies
            rates = self.extract_from_tables()
            if not rates:
                rates = self.extract_from_page_text()

            if rates:
                return self.format_rates(rates)

            return None

        except Exception as e:
            print(f"✗ Error during scraping: {e}")
            return None

        finally:
            if self.driver:
                self.driver.quit()
                print("✓ Browser closed")

    def format_rates(self, raw_rates):
        """Format rates into standard structure with supply charges only."""
        formatted = {
            "effective_date": datetime.now().strftime("%Y-%m-%d"),
            "last_updated": datetime.now().isoformat(),
            "standard": {},
            "time_of_use": {"on_peak": {}, "off_peak": {}},
        }

        # These are supply charges only from the website
        if "residential_supply" in raw_rates:
            formatted["standard"]["supply_charge"] = raw_rates["residential_supply"]
            formatted["standard"]["description"] = (
                "Standard residential supply charge (delivery charge must be added separately)"
            )

        if "on_peak_supply" in raw_rates:
            formatted["time_of_use"]["on_peak"]["supply_charge"] = raw_rates[
                "on_peak_supply"
            ]
            formatted["time_of_use"]["on_peak"]["description"] = (
                "Time-of-Use on-peak supply charge (delivery charge must be added separately)"
            )

        if "off_peak_supply" in raw_rates:
            formatted["time_of_use"]["off_peak"]["supply_charge"] = raw_rates[
                "off_peak_supply"
            ]
            formatted["time_of_use"]["off_peak"]["description"] = (
                "Time-of-Use off-peak supply charge (delivery charge must be added separately)"
            )

        return formatted


def save_prices(
    new_rate, output_file="../custom_components/central_hudson/data/prices.json"
):
    """Save prices to JSON file."""
    if not new_rate:
        return False

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        with open(output_path) as f:
            data = json.load(f)
    else:
        data = {"customer_charge": 22.50, "rates": []}

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

    data["rates"].sort(key=lambda x: x.get("effective_date", ""), reverse=True)

    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✓ Saved to {output_file}")
    print(f"  Total historical rates: {len(data['rates'])}")
    print("\nCurrent rate:")
    print(json.dumps(data["rates"][0], indent=2))
    return True


def main():
    """Main entry point."""
    print("=" * 60)
    print("Central Hudson Selenium Scraper")
    print("=" * 60)
    print()

    # Check for --visible flag
    headless = "--visible" not in sys.argv

    scraper = SeleniumScraper(headless=headless)
    rates = scraper.fetch_prices()

    if rates:
        print("\n" + "=" * 60)
        print("Extracted Rates:")
        print("=" * 60)
        print(json.dumps(rates, indent=2))

        if save_prices(rates):
            print("\n✓ Success!")
            return 0
        else:
            print("\n✗ Failed to save")
            return 1
    else:
        print("\n✗ Failed to extract rates")
        print("\nTry running with --visible flag to see the browser")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
