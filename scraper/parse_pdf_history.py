#!/usr/bin/env python3
"""
Parse Central Hudson PDF to extract historical electricity rates.
This script extracts all available historical rates from the PDF.
"""
import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


# Fixed delivery charges (these don't change monthly like supply charges)
DELIVERY_CHARGES = {
    "standard": 0.13860,
    "on_peak": 0.14732,
    "off_peak": 0.12739
}

CUSTOMER_CHARGE = 22.50


def parse_pdf(pdf_path):
    """Extract text from PDF using pdftotext."""
    try:
        result = subprocess.run(
            ['pdftotext', pdf_path, '-'],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error extracting PDF text: {e}", file=sys.stderr)
        return None
    except FileNotFoundError:
        print("pdftotext not found. Please install poppler-utils.", file=sys.stderr)
        return None


def parse_date(date_str):
    """Convert 'Feb. 11, 2026' to '2026-02-11'."""
    try:
        # Remove period after month abbreviation
        date_str = date_str.replace('.', '')
        # Handle "Sept" vs "Sep"
        date_str = date_str.replace('Sept', 'Sep')
        dt = datetime.strptime(date_str, '%b %d, %Y')
        return dt.strftime('%Y-%m-%d')
    except ValueError as e:
        print(f"Error parsing date '{date_str}': {e}", file=sys.stderr)
        return None


def extract_rates(pdf_text):
    """Extract historical rates from PDF text."""
    rates = []

    # Pattern to match date lines followed by rates
    # Looking for lines like "Feb. 11, 2026" followed by price lines
    lines = pdf_text.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check if this is a date line
        date_match = re.match(r'^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\.\s+\d{1,2},\s+202[56]', line)

        if date_match:
            effective_date = parse_date(line)
            if not effective_date:
                i += 1
                continue

            # Look ahead for the three rate values
            # Skip empty lines
            j = i + 1
            values = []
            while j < len(lines) and len(values) < 3:
                next_line = lines[j].strip()
                if next_line and next_line.startswith('$'):
                    # Extract numeric value
                    price_match = re.search(r'\$([0-9]+\.[0-9]+)', next_line)
                    if price_match:
                        values.append(float(price_match.group(1)))
                j += 1

            if len(values) >= 3:
                standard_supply = values[0]
                onpeak_supply = values[1]
                offpeak_supply = values[2]

                rate_entry = {
                    "effective_date": effective_date,
                    "last_updated": datetime.now().isoformat(),
                    "standard": {
                        "supply_charge": standard_supply,
                        "delivery_charge": DELIVERY_CHARGES["standard"],
                        "total_per_kwh": round(standard_supply + DELIVERY_CHARGES["standard"], 5),
                        "description": "Standard residential rate (supply + delivery)"
                    },
                    "time_of_use": {
                        "on_peak": {
                            "supply_charge": onpeak_supply,
                            "delivery_charge": DELIVERY_CHARGES["on_peak"],
                            "total_per_kwh": round(onpeak_supply + DELIVERY_CHARGES["on_peak"], 5),
                            "description": "Time-of-Use on-peak rate (supply + delivery)"
                        },
                        "off_peak": {
                            "supply_charge": offpeak_supply,
                            "delivery_charge": DELIVERY_CHARGES["off_peak"],
                            "total_per_kwh": round(offpeak_supply + DELIVERY_CHARGES["off_peak"], 5),
                            "description": "Time-of-Use off-peak rate (supply + delivery)"
                        }
                    }
                }

                rates.append(rate_entry)
                print(f"Extracted rate for {effective_date}: Standard=${standard_supply}, On-Peak=${onpeak_supply}, Off-Peak=${offpeak_supply}")

        i += 1

    return rates


def save_historical_rates(rates, output_file='../custom_components/central_hudson/data/prices.json'):
    """Save all historical rates to JSON file."""
    if not rates:
        print("No rates to save", file=sys.stderr)
        return False

    # Sort rates by effective_date (most recent first)
    rates.sort(key=lambda x: x.get('effective_date', ''), reverse=True)

    data = {
        "customer_charge": CUSTOMER_CHARGE,
        "rates": rates
    }

    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"\nSaved {len(rates)} historical rates to {output_file}")
    print(f"Date range: {rates[-1]['effective_date']} to {rates[0]['effective_date']}")
    return True


if __name__ == '__main__':
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else '/home/sdague/Downloads/Gas & Electric Supply Prices.pdf'

    print(f"Parsing PDF: {pdf_path}")
    pdf_text = parse_pdf(pdf_path)

    if not pdf_text:
        sys.exit(1)

    print("Extracting historical rates...")
    rates = extract_rates(pdf_text)

    if rates:
        save_historical_rates(rates)
        print("\n✓ Historical rates successfully extracted and saved!")
        sys.exit(0)
    else:
        print("No rates found in PDF", file=sys.stderr)
        sys.exit(1)
