#!/usr/bin/env python3
"""
Scraper script to fetch Central Hudson electricity prices.
Run this monthly to update the prices data file.
"""
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import sys


def fetch_prices():
    """Fetch electricity prices from Central Hudson website."""
    url = "https://www.cenhud.com/en/account-resources/rates/gas--electric-supply-prices/"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }

    try:
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')

        # Extract price data from the page
        # This will need to be adjusted based on the actual HTML structure
        prices = {
            'last_updated': datetime.now().isoformat(),
            'residential': {},
            'commercial': {}
        }

        # Look for price tables or specific elements
        # Example structure - adjust based on actual page:
        tables = soup.find_all('table')

        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True)

                    # Try to extract numeric price
                    try:
                        # Remove $ and convert to float
                        price_value = float(value.replace('$', '').replace('¢', '').strip())

                        if 'residential' in label or 'res' in label:
                            if 'kwh' in label or 'kilowatt' in label:
                                prices['residential']['per_kwh'] = price_value
                        elif 'commercial' in label or 'comm' in label:
                            if 'kwh' in label or 'kilowatt' in label:
                                prices['commercial']['per_kwh'] = price_value
                    except ValueError:
                        continue

        return prices

    except requests.RequestException as e:
        print(f"Error fetching prices: {e}", file=sys.stderr)
        return None


def save_prices(prices, output_file='../custom_components/central_hudson/data/prices.json'):
    """Save prices to JSON file."""
    if prices:
        with open(output_file, 'w') as f:
            json.dump(prices, f, indent=2)
        print(f"Prices saved to {output_file}")
        print(json.dumps(prices, indent=2))
        return True
    return False


if __name__ == '__main__':
    print("Fetching Central Hudson electricity prices...")
    prices = fetch_prices()

    if prices:
        save_prices(prices)
        sys.exit(0)
    else:
        print("Failed to fetch prices. Please check the website manually.", file=sys.stderr)
        sys.exit(1)

# Made with Bob
