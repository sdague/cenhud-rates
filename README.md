# Central Hudson Electric Rates

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)

A Home Assistant custom component that provides Central Hudson electricity rate information as sensors.

## Features

- Monitor current electricity rates for residential and commercial customers
- Rates update monthly from Central Hudson's website
- Easy configuration through Home Assistant UI
- HACS compatible

## Installation

### HACS (Recommended)

1. Open HACS in your Home Assistant instance
2. Click on "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add this repository URL: `https://github.com/sdague/central-hudson-electric-rates`
6. Select category "Integration"
7. Click "Add"
8. Find "Central Hudson Electric Rates" in the integration list and click "Download"
9. Restart Home Assistant

### Manual Installation

1. Copy the `custom_components/central_hudson` directory to your Home Assistant's `custom_components` directory
2. Restart Home Assistant

## Configuration

1. Go to Settings → Devices & Services
2. Click "+ Add Integration"
3. Search for "Central Hudson Electric Rates"
4. Select your rate type (Residential or Commercial)
5. Click "Submit"

## Sensors

The integration creates a sensor entity:

- **Residential Electric Rate** or **Commercial Electric Rate**: Current electricity rate in $/kWh

### Sensor Attributes

- `rate_type`: The type of rate (residential or commercial)
- `last_updated`: When the price data was last updated

## Updating Prices

Prices are stored in a JSON file and need to be updated monthly. To update:

1. Navigate to the `scraper` directory
2. Install requirements: `pip install -r requirements.txt`
3. Run the scraper: `python fetch_prices.py`
4. Commit the updated `custom_components/central_hudson/data/prices.json` file

The scraper fetches current rates from the Central Hudson website at:
https://www.cenhud.com/en/account-resources/rates/gas--electric-supply-prices/

## Energy Dashboard Integration

You can use this sensor in Home Assistant's Energy Dashboard:

1. Go to Settings → Dashboards → Energy
2. Under "Electricity grid" → "Grid consumption"
3. Click "Add consumption"
4. Select your electricity consumption sensor
5. For "Use an entity tracking the total costs", select the Central Hudson rate sensor

## Troubleshooting

### Prices showing as 0.0

Run the scraper script to fetch current prices:
```bash
cd scraper
pip install -r requirements.txt
python fetch_prices.py
```

### Integration not appearing

1. Ensure you've copied all files correctly
2. Check Home Assistant logs for errors
3. Restart Home Assistant

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Disclaimer

This is an unofficial integration and is not affiliated with Central Hudson Gas & Electric Corp. Rate information is provided as-is and should be verified with official Central Hudson sources.