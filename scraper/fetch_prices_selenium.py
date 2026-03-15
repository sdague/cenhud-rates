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

    def extract_date(self, text):
        """Extract date from text in format like 'Feb 11, 2026' or 'February 11, 2026'."""
        if not text:
            return None

        # Month name mapping
        months = {
            "jan": 1,
            "january": 1,
            "feb": 2,
            "february": 2,
            "mar": 3,
            "march": 3,
            "apr": 4,
            "april": 4,
            "may": 5,
            "jun": 6,
            "june": 6,
            "jul": 7,
            "july": 7,
            "aug": 8,
            "august": 8,
            "sep": 9,
            "september": 9,
            "oct": 10,
            "october": 10,
            "nov": 11,
            "november": 11,
            "dec": 12,
            "december": 12,
        }

        # Try to parse date format like "Feb 11, 2026"
        match = re.search(r"(\w+)\s+(\d{1,2}),?\s+(\d{4})", text.lower())
        if match:
            month_str, day, year = match.groups()
            month = months.get(month_str[:3])
            if month:
                try:
                    date_obj = datetime(int(year), month, int(day))
                    return date_obj.strftime("%Y-%m-%d")
                except ValueError:
                    pass

        return None

    def get_latest_delivery_charges(self):
        """Get delivery charges from the most recent historical data."""
        try:
            prices_file = (
                Path(__file__).parent.parent
                / "custom_components"
                / "central_hudson"
                / "data"
                / "prices.json"
            )
            if prices_file.exists():
                with open(prices_file) as f:
                    data = json.load(f)
                    rates = data.get("rates", [])
                    if rates:
                        # Get the most recent rate with delivery charges
                        for rate in rates:
                            standard = rate.get("standard", {})
                            tou = rate.get("time_of_use", {})

                            if "delivery_charge" in standard:
                                return {
                                    "standard": standard.get("delivery_charge"),
                                    "on_peak": tou.get("on_peak", {}).get(
                                        "delivery_charge"
                                    ),
                                    "off_peak": tou.get("off_peak", {}).get(
                                        "delivery_charge"
                                    ),
                                }
        except Exception as e:
            print(f"  Warning: Could not load delivery charges: {e}")

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
                            label = cells[0].text.strip()
                            label_lower = label.lower()

                            # Skip the 12-month average row (contains "avg")
                            if "avg" in label_lower or "average" in label_lower:
                                print(f"    Skipping average row: {label}")
                                continue

                            # Look for rows with actual month names
                            if any(
                                month in label_lower
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
                                # Skip if we already found rates (first data row is what we want)
                                if rates:
                                    print(f"    Skipping additional row: {label}")
                                    continue

                                print(f"    Processing row: {label}")
                                print(f"      Row has {len(cells)} cells")

                                # Extract effective date from first column
                                effective_date = self.extract_date(label)
                                if effective_date:
                                    rates["effective_date"] = effective_date
                                    print(f"      Effective date: {effective_date}")

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
                    line_lower = line.lower()

                    # Skip the 12-month average row
                    if "avg" in line_lower or "average" in line_lower:
                        print(f"  Skipping average row: {line}")
                        continue

                    # Check if this line has a date pattern (month name)
                    if any(
                        month in line_lower
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
                        # Skip if we already found rates
                        if rates:
                            print(f"  Skipping additional row: {line}")
                            continue

                        print(f"  Found data row: {line}")

                        # Extract effective date
                        effective_date = self.extract_date(line)
                        if effective_date:
                            rates["effective_date"] = effective_date
                            print(f"    Effective date: {effective_date}")

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
        """Format rates into standard structure with supply and delivery charges."""
        # Use extracted effective date or default to today
        effective_date = raw_rates.get(
            "effective_date", datetime.now().strftime("%Y-%m-%d")
        )

        formatted = {
            "effective_date": effective_date,
            "last_updated": datetime.now().isoformat(),
            "standard": {},
            "time_of_use": {"on_peak": {}, "off_peak": {}},
        }

        # Get delivery charges from historical data
        delivery_charges = self.get_latest_delivery_charges()

        # Format standard rate
        if "residential_supply" in raw_rates:
            formatted["standard"]["supply_charge"] = raw_rates["residential_supply"]

            if delivery_charges and delivery_charges.get("standard"):
                formatted["standard"]["delivery_charge"] = delivery_charges["standard"]
                formatted["standard"]["total_per_kwh"] = round(
                    raw_rates["residential_supply"] + delivery_charges["standard"], 5
                )
                formatted["standard"]["description"] = (
                    "Standard residential rate (supply + delivery)"
                )
            else:
                formatted["standard"]["description"] = (
                    "Standard residential supply charge (delivery charge must be added separately)"
                )

        # Format on-peak rate
        if "on_peak_supply" in raw_rates:
            formatted["time_of_use"]["on_peak"]["supply_charge"] = raw_rates[
                "on_peak_supply"
            ]

            if delivery_charges and delivery_charges.get("on_peak"):
                formatted["time_of_use"]["on_peak"]["delivery_charge"] = (
                    delivery_charges["on_peak"]
                )
                formatted["time_of_use"]["on_peak"]["total_per_kwh"] = round(
                    raw_rates["on_peak_supply"] + delivery_charges["on_peak"], 5
                )
                formatted["time_of_use"]["on_peak"]["description"] = (
                    "Time-of-Use on-peak rate (supply + delivery)"
                )
            else:
                formatted["time_of_use"]["on_peak"]["description"] = (
                    "Time-of-Use on-peak supply charge (delivery charge must be added separately)"
                )

        # Format off-peak rate
        if "off_peak_supply" in raw_rates:
            formatted["time_of_use"]["off_peak"]["supply_charge"] = raw_rates[
                "off_peak_supply"
            ]

            if delivery_charges and delivery_charges.get("off_peak"):
                formatted["time_of_use"]["off_peak"]["delivery_charge"] = (
                    delivery_charges["off_peak"]
                )
                formatted["time_of_use"]["off_peak"]["total_per_kwh"] = round(
                    raw_rates["off_peak_supply"] + delivery_charges["off_peak"], 5
                )
                formatted["time_of_use"]["off_peak"]["description"] = (
                    "Time-of-Use off-peak rate (supply + delivery)"
                )
            else:
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
