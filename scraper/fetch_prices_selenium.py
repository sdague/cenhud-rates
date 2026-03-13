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
            return True
        except Exception as e:
            print(f"✗ Timeout waiting for content: {e}")
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
            tables = self.driver.find_elements(By.TAG_NAME, "table")
            print(f"  Found {len(tables)} tables")

            for _table_idx, table in enumerate(tables):
                rows = table.find_elements(By.TAG_NAME, "tr")

                for row in rows:
                    try:
                        cells = row.find_elements(By.TAG_NAME, "td")
                        if not cells:
                            cells = row.find_elements(By.TAG_NAME, "th")

                        if len(cells) >= 2:
                            label = cells[0].text.strip().lower()
                            value_text = cells[1].text.strip()
                            price = self.extract_price(value_text)

                            if price and label:
                                print(f"    Found: {label} = {price}")

                                if any(
                                    kw in label
                                    for kw in [
                                        "residential",
                                        "standard",
                                        "service class 1",
                                    ]
                                ):
                                    if "kwh" in label:
                                        rates["residential_per_kwh"] = price
                                elif "commercial" in label:
                                    if "kwh" in label:
                                        rates["commercial_per_kwh"] = price
                                elif "on-peak" in label or "on peak" in label:
                                    if "kwh" in label:
                                        rates["on_peak_per_kwh"] = price
                                elif "off-peak" in label or "off peak" in label:
                                    if "kwh" in label:
                                        rates["off_peak_per_kwh"] = price
                    except Exception:
                        continue

        except Exception as e:
            print(f"  Error extracting from tables: {e}")

        return rates if rates else None

    def extract_from_page_text(self):
        """Extract prices from all page text."""
        print("Extracting from page text...")
        rates = {}

        try:
            page_text = self.driver.find_element(By.TAG_NAME, "body").text

            patterns = [
                (r"residential[:\s]+\$?([\d.]+)\s*[¢/]*\s*kwh", "residential_per_kwh"),
                (r"commercial[:\s]+\$?([\d.]+)\s*[¢/]*\s*kwh", "commercial_per_kwh"),
                (r"on[- ]peak[:\s]+\$?([\d.]+)\s*[¢/]*\s*kwh", "on_peak_per_kwh"),
                (r"off[- ]peak[:\s]+\$?([\d.]+)\s*[¢/]*\s*kwh", "off_peak_per_kwh"),
            ]

            for pattern, rate_key in patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    price = self.extract_price(match.group(1))
                    if price:
                        print(f"    Found {rate_key}: {price}")
                        rates[rate_key] = price
                        break

        except Exception as e:
            print(f"  Error extracting from text: {e}")

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
        """Format rates into standard structure."""
        formatted = {
            "effective_date": datetime.now().strftime("%Y-%m-%d"),
            "last_updated": datetime.now().isoformat(),
            "standard": {},
            "time_of_use": {"on_peak": {}, "off_peak": {}},
        }

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
