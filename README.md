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
- `data/indicators/gdp_by_industry_annual.csv`: long-format annual real gross
  value added for 16 major industries, total value added at basic prices, net
  product-tax bridge components, and GDP at market prices. Values are millions
  of 2004 pesos.
- `data/indicators/fiscal_primary_balance.csv`: monthly primary balance for the
  nonfinancial National Public Sector in nominal millions of pesos and real
  December 2016 millions of pesos. The real series uses the official national
  CPI and therefore begins in December 2016.
- `data/series/*.json`: full metadata and up to 1,000 observations for each series
  used by a group or listed in `config/series.txt`.

The GitHub Actions workflow runs every day at 10:17 UTC and can also be started
manually from the repository's **Actions** tab. It commits only when the API data
has changed.

## Track series values

Edit `config/series_groups.json` to add grouped, wide-format CSV outputs. Each
group maps readable column names to API series IDs. Add standalone IDs to
`config/series.txt` when only the full JSON response is needed.

Edit `config/long_series_groups.json` to configure long-format outputs. The
updater checks that the industry components sum to value added at basic prices
and that value added plus the product-tax bridge sums to GDP before replacing
the published CSV.

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
