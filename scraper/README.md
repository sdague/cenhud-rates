# Central Hudson Price Scraper

Tools for fetching electricity rates from the Central Hudson website.

## Available Scrapers

### 1. fetch_prices.py (Original - Simple)
Basic scraper using requests and BeautifulSoup.

**Pros:**
- Fast and lightweight
- No browser required
- Works for static HTML

**Cons:**
- May fail on JavaScript-heavy pages
- Limited to visible HTML content

**Usage:**
```bash
cd scraper
pip install -r requirements.txt
python fetch_prices.py
```

### 2. fetch_prices_improved.py (Recommended)
Multi-strategy scraper with fallback methods.

**Features:**
- 4 different extraction strategies
- Automatic fallback if one method fails
- Better error handling and logging
- Detailed output for debugging

**Strategies:**
1. HTML table extraction
2. Div/span element search
3. Text pattern matching
4. API endpoint detection

**Usage:**
```bash
cd scraper
pip install -r requirements.txt
python fetch_prices_improved.py
```

### 3. fetch_prices_selenium.py (Recommended - Working)
Uses Selenium for JavaScript-rendered content.

**Status:** ✅ **WORKING** - This is the recommended scraper as of March 2026.

**Why this scraper is needed:**
The Central Hudson website loads pricing data dynamically using JavaScript after the initial page load. The pricing table is not present in the initial HTML response, which is why requests-based scrapers (fetch_prices.py and fetch_prices_improved.py) cannot extract the data reliably.

**How it works:**
1. Launches a headless Chrome browser
2. Navigates to the pricing page
3. Waits for the page to load and scrolls to trigger content loading
4. Waits for pricing data to appear (looks for "$0." text patterns)
5. Extracts data from the dynamically-loaded HTML table
6. Saves rates to prices.json

**Requirements:**
```bash
pip install -r requirements.txt
# This now includes selenium and webdriver-manager
```

**Usage:**
```bash
# Headless mode (default, recommended)
python fetch_prices_selenium.py

# Visible browser (for debugging)
python fetch_prices_selenium.py --visible
```

**What it extracts:**
- Standard residential rate ($/kWh)
- Time-of-Use on-peak rate ($/kWh)
- Time-of-Use off-peak rate ($/kWh)

## Output

All scrapers save data to:
```
../custom_components/central_hudson/data/prices.json
```

Format:
```json
{
  "customer_charge": 22.50,
  "rates": [
    {
      "effective_date": "2026-03-13",
      "last_updated": "2026-03-13T10:00:00",
      "standard": {
        "total_per_kwh": 0.12345
      },
      "time_of_use": {
        "on_peak": {
          "total_per_kwh": 0.15000
        },
        "off_peak": {
          "total_per_kwh": 0.10000
        }
      }
    }
  ]
}
```

## Troubleshooting

### Scraper Returns No Data

**As of March 2026:** The Central Hudson website uses dynamic JavaScript to load pricing data. Only the Selenium scraper (fetch_prices_selenium.py) works reliably.

1. **Use the Selenium scraper (recommended):**
   ```bash
   python fetch_prices_selenium.py
   ```

2. **If Selenium scraper fails:**
   - Check the website manually: https://www.cenhud.com/en/account-resources/rates/gas--electric-supply-prices/
   - Try with visible browser to see what's happening:
     ```bash
     python fetch_prices_selenium.py --visible
     ```
   - Check the generated `scraper_screenshot.png` and `scraper_page.html` for debugging

3. **Check for website changes:**
   The website structure may have changed. You may need to update the scraper logic.

4. **Why other scrapers don't work:**
   - `fetch_prices.py` and `fetch_prices_improved.py` use requests/BeautifulSoup
   - These tools only see the initial HTML, not JavaScript-rendered content
   - The pricing table is loaded dynamically after page load
   - Selenium is required to wait for and extract the dynamic content

### Common Issues

**Issue: "No module named 'requests'"**
```bash
pip install -r requirements.txt
```

**Issue: "No module named 'selenium'"**
```bash
pip install selenium webdriver-manager
```

**Issue: "ChromeDriver not found"**
The Selenium scraper automatically downloads ChromeDriver. If it fails:
```bash
# Install Chrome/Chromium first
# Then run the scraper again
```

**Issue: "All strategies failed"**
If using fetch_prices.py or fetch_prices_improved.py:
- These scrapers don't work with the current website (as of March 2026)
- Use fetch_prices_selenium.py instead

If using fetch_prices_selenium.py and it fails:
1. Run with `--visible` flag to see what's happening
2. Check `scraper_screenshot.png` to see if the table loaded
3. Check `scraper_page.html` to see the page source
4. The website structure may have changed - update the extraction logic

## Manual Price Updates

If scrapers fail, you can manually update `prices.json`:

```json
{
  "customer_charge": 22.50,
  "rates": [
    {
      "effective_date": "2026-03-13",
      "last_updated": "2026-03-13T10:00:00.000000",
      "standard": {
        "total_per_kwh": 0.12345
      },
      "time_of_use": {
        "on_peak": {
          "total_per_kwh": 0.15000
        },
        "off_peak": {
          "total_per_kwh": 0.10000
        }
      }
    }
  ]
}
```

## Development

### Adding New Extraction Strategies

Edit `fetch_prices_improved.py` and add a new strategy method:

```python
def strategy_5_your_method(self, soup):
    """Your new extraction strategy."""
    rates = {}
    # Your extraction logic here
    return rates if rates else None
```

Then add it to the strategies list in `fetch_prices()`.

### Testing

Test the scraper without saving:

```python
from fetch_prices_improved import CentralHudsonScraper

scraper = CentralHudsonScraper()
rates = scraper.fetch_prices()
print(rates)
```

## Automation

### Monthly Cron Job

Add to crontab to run monthly:

```bash
# Run on the 1st of each month at 9 AM
0 9 1 * * cd /path/to/scraper && python fetch_prices_improved.py
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
          python fetch_prices_improved.py
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
   - Screenshot of the website
   - Error messages
3. Consider contributing an improved scraper!