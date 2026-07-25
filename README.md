# GOV_ARG_TS

Daily, focused economic snapshots from Argentina's official Time Series API.

## What is updated

- `data/categories/government_finance.csv`: government finance series.
- `data/categories/inflation_prices.csv`: inflation and price series.
- `data/categories/economic_activity.csv`: economic activity series.
- `data/categories/employment_income.csv`: employment and income series.
- `data/categories/external_sector.csv`: external-sector series.
- `data/categories/money_banking.csv`: money and banking series.
- `data/series/*.json`: full metadata and up to 1,000 observations for each series
  listed in `config/series.txt`.

The GitHub Actions workflow runs every day at 10:17 UTC and can also be started
manually from the repository's **Actions** tab. It commits only when the API data
has changed.

## Track series values

1. Find the desired `series_id` in one of the category CSVs.
2. Add that ID on its own line in `config/series.txt`.
3. Commit the change. The next run will create a JSON file under `data/series/`.

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
