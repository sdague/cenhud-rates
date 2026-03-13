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

### 3. fetch_prices_selenium.py (Advanced)
Uses Selenium for JavaScript-rendered content.

**When to use:**
- When other scrapers fail
- When content loads dynamically
- When you need to interact with the page (click tabs, etc.)

**Requirements:**
```bash
pip install selenium webdriver-manager
```

**Usage:**
```bash
# Headless mode (default)
python fetch_prices_selenium.py

# Visible browser (for debugging)
python fetch_prices_selenium.py --visible
```

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

1. **Check the website manually:**
   Visit: https://www.cenhud.com/en/account-resources/rates/gas--electric-supply-prices/

2. **Try the improved scraper:**
   ```bash
   python fetch_prices_improved.py
   ```

3. **Try Selenium scraper with visible browser:**
   ```bash
   python fetch_prices_selenium.py --visible
   ```
   Watch what happens and see where it fails.

4. **Check for website changes:**
   The website structure may have changed. You may need to update the scraper logic.

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
The website structure has likely changed. You'll need to:
1. Inspect the website HTML
2. Update the extraction logic in the scraper
3. Or manually update prices.json

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