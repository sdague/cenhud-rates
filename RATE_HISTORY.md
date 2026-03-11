# Central Hudson Electric Rate History

This file documents the historical electricity rates for Central Hudson customers.

## How to Add New Rates

When new rates are published (typically monthly), you can add them in two ways:

### Option 1: Manual Update
Edit `custom_components/central_hudson/data/prices.json` and add a new entry to the `rates` array:

```json
{
  "effective_date": "YYYY-MM-DD",
  "last_updated": "YYYY-MM-DDTHH:MM:SS-05:00",
  "standard": {
    "supply_charge": 0.xxxxx,
    "delivery_charge": 0.xxxxx,
    "total_per_kwh": 0.xxxxx,
    "description": "Standard residential rate (supply + delivery)"
  },
  "time_of_use": {
    "on_peak": {
      "supply_charge": 0.xxxxx,
      "delivery_charge": 0.xxxxx,
      "total_per_kwh": 0.xxxxx,
      "description": "Time-of-Use on-peak rate (supply + delivery)"
    },
    "off_peak": {
      "supply_charge": 0.xxxxx,
      "delivery_charge": 0.xxxxx,
      "total_per_kwh": 0.xxxxx,
      "description": "Time-of-Use off-peak rate (supply + delivery)"
    }
  }
}
```

The integration will automatically use the most recent rate based on `effective_date`.

### Option 2: Run Scraper
```bash
cd scraper
python fetch_prices.py
```

The scraper will attempt to fetch rates from the Central Hudson website and append them to the historical data.

## Rate History

### February 2026 (Effective: 2026-02-11)

**Supply Charges:**
- Standard: $0.14849/kWh
- On-Peak: $0.27466/kWh
- Off-Peak: $0.21981/kWh

**Delivery Charges:**
- Standard: $0.13860/kWh
- On-Peak: $0.14732/kWh
- Off-Peak: $0.12739/kWh

**Total Rates (Supply + Delivery):**
- Standard: $0.28709/kWh
- On-Peak: $0.42198/kWh
- Off-Peak: $0.34720/kWh

**Customer Charge:** $22.50/month

---

## Notes

- Rates are sorted by effective date (most recent first) in the JSON file
- The integration always uses the most recent rate
- Historical data is preserved for record-keeping
- Customer charge is stored at the top level as it typically doesn't change monthly