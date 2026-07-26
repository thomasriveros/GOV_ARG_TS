# GOV_ARG_TS

Daily, focused economic snapshots from Argentina's official Time Series API.

## What is updated

- `data/categories/government_finance.csv`: government finance series.
- `data/categories/inflation_prices.csv`: inflation and price series.
- `data/categories/economic_activity.csv`: economic activity series.
- `data/categories/employment_income.csv`: employment and income series.
- `data/categories/external_sector.csv`: external-sector series.
- `data/categories/money_banking.csv`: money and banking series.
- `data/indicators/gdp_expenditure.csv`: real GDP and expenditure components.
- `data/indicators/gdp_expenditure_seasonally_adjusted.csv`: seasonally adjusted
  real GDP and expenditure components.
- `data/indicators/gdp_production_sectors.csv`: real GDP by major production sector.
- `data/series/*.json`: full metadata and up to 1,000 observations for each series
  used by a group or listed in `config/series.txt`.

The GitHub Actions workflow runs every day at 10:17 UTC and can also be started
manually from the repository's **Actions** tab. It commits only when the API data
has changed.

## Track series values

Edit `config/series_groups.json` to add grouped, wide-format CSV outputs. Each
group maps readable column names to API series IDs. Add standalone IDs to
`config/series.txt` when only the full JSON response is needed.

Edit `config/categories.json` to add, remove, or rename category exports. Values
must exactly match the API's official theme names.

The API limits a single series response to 1,000 observations. Every category is
paginated automatically and checked for completeness before files are replaced.

## Run locally

Python 3.10 or newer is the only requirement:

```bash
python scripts/update_data.py
```

## Source

- [Official API documentation](https://datosgobar.github.io/series-tiempo-ar-api/)
- [Complete API reference](https://www.argentina.gob.ar/innovacion-ciencia-y-tecnologia/gobierno-abierto/datos-abiertos/api-series-de-tiempo/referencia-completa-de-la-api-series-de-tiempo)
- API base URL: `https://apis.datos.gob.ar/series/api`
