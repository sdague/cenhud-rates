# Central Hudson Price Scraper

Tool for fetching electricity rates from the Central Hudson website.

## Scraper

### fetch_prices_selenium.py

Uses Selenium for JavaScript-rendered content.

**Status:** ✅ **WORKING** - This is the only scraper as of March 2026.

**Why Selenium is needed:**
The Central Hudson website loads pricing data dynamically using JavaScript after the initial page load. The pricing table is not present in the initial HTML response, which is why requests-based scrapers cannot extract the data reliably.

**How it works:**
1. Launches a headless Chrome browser
2. Navigates to the pricing page
3. Waits for the page to load and scrolls to trigger content loading
4. Waits for pricing data to appear (looks for "$0." text patterns)
5. Skips the 12-month average row
6. Extracts the first data row (most recent month) from the dynamically-loaded HTML table
7. Extracts the effective date from the first column
8. Fetches delivery charges from historical data
9. Calculates total per kWh (supply + delivery)
10. Saves rates to prices.json

**Requirements:**
```bash
pip install -r requirements.txt
# This includes selenium and webdriver-manager
```

**Usage:**
```bash
# Headless mode (default, recommended)
python fetch_prices_selenium.py

# Visible browser (for debugging)
python fetch_prices_selenium.py --visible
```

**What it extracts:**
- Effective date from the pricing table
- Standard residential supply charge ($/kWh)
- Time-of-Use on-peak supply charge ($/kWh)
- Time-of-Use off-peak supply charge ($/kWh)
- Delivery charges from historical data
- Total per kWh (supply + delivery) for all rate types

## Output

The scraper saves data to:
```
../custom_components/central_hudson/data/prices.json
```

Format:
```json
{
  "customer_charge": 22.50,
  "rates": [
    {
      "effective_date": "2026-03-12",
      "last_updated": "2026-03-15T06:52:48.029735",
      "standard": {
        "supply_charge": 0.14228,
        "delivery_charge": 0.1386,
        "total_per_kwh": 0.28088,
        "description": "Standard residential rate (supply + delivery)"
      },
      "time_of_use": {
        "on_peak": {
          "supply_charge": 0.1832,
          "delivery_charge": 0.14732,
          "total_per_kwh": 0.33052,
          "description": "Time-of-Use on-peak rate (supply + delivery)"
        },
        "off_peak": {
          "supply_charge": 0.13575,
          "delivery_charge": 0.12739,
          "total_per_kwh": 0.26314,
          "description": "Time-of-Use off-peak rate (supply + delivery)"
        }
      }
    }
  ]
}
```

## Troubleshooting

### Scraper Returns No Data

1. **Check the website manually:** https://www.cenhud.com/en/account-resources/rates/gas--electric-supply-prices/

2. **Try with visible browser to see what's happening:**
   ```bash
   python fetch_prices_selenium.py --visible
   ```

3. **Check debugging files:**
   - `scraper_screenshot.png` - Screenshot of the page when scraping
   - `scraper_page.html` - HTML source of the page

4. **Check for website changes:**
   The website structure may have changed. You may need to update the scraper logic.

### Common Issues

**Issue: "No module named 'selenium'"**
```bash
pip install -r requirements.txt
```

**Issue: "ChromeDriver not found"**
The scraper automatically downloads ChromeDriver. If it fails:
```bash
# Install Chrome/Chromium first
# Then run the scraper again
```

**Issue: Scraper extracts wrong data**
- Check if the website changed its table structure
- Look at `scraper_screenshot.png` to see what the page looks like
- Check `scraper_page.html` to see the HTML structure
- Update the extraction logic in `fetch_prices_selenium.py` if needed

## Manual Price Updates

If the scraper fails, you can manually update `prices.json`:

```json
{
  "customer_charge": 22.50,
  "rates": [
    {
      "effective_date": "2026-03-12",
      "last_updated": "2026-03-15T10:00:00.000000",
      "standard": {
        "supply_charge": 0.14228,
        "delivery_charge": 0.1386,
        "total_per_kwh": 0.28088,
        "description": "Standard residential rate (supply + delivery)"
      },
      "time_of_use": {
        "on_peak": {
          "supply_charge": 0.1832,
          "delivery_charge": 0.14732,
          "total_per_kwh": 0.33052,
          "description": "Time-of-Use on-peak rate (supply + delivery)"
        },
        "off_peak": {
          "supply_charge": 0.13575,
          "delivery_charge": 0.12739,
          "total_per_kwh": 0.26314,
          "description": "Time-of-Use off-peak rate (supply + delivery)"
        }
      }
    }
  ]
}
```

## Automation

### Monthly Cron Job

Add to crontab to run monthly:

```bash
# Run on the 1st of each month at 9 AM
0 9 1 * * cd /path/to/scraper && python fetch_prices_selenium.py
```

### GitHub Actions

Create `.github/workflows/update-prices.yml`:

```yaml
name: Update Prices

on:
  schedule:
    - cron: '0 9 1 * *'  # Monthly on 1st at 9 AM
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: |
          cd scraper
          pip install -r requirements.txt
      - name: Fetch prices
        run: |
          cd scraper
          python fetch_prices_selenium.py
      - name: Commit changes
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add custom_components/central_hudson/data/prices.json
          git commit -m "Update electricity prices" || echo "No changes"
          git push
```

## Support

If you continue to have issues:

1. Check the [GitHub Issues](https://github.com/sdague/cenhud-rates/issues)
2. Open a new issue with:
   - Scraper output
   - Screenshot of the website (`scraper_screenshot.png`)
   - HTML source (`scraper_page.html`)
   - Error messages
3. Consider contributing improvements to the scraper!