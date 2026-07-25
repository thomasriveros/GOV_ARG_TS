#!/usr/bin/env python3
"""Refresh selected categories from Argentina's government time-series API."""

from __future__ import annotations

import argparse
import csv
import io
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_API_URL = "https://apis.datos.gob.ar/series/api"
USER_AGENT = "GOV_ARG_TS/1.0 (+https://github.com/thomasriveros/GOV_ARG_TS)"


def request_json(url: str, attempts: int = 5) -> dict:
    """Fetch JSON with bounded exponential backoff."""
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            request = urllib.request.Request(
                url, headers={"Accept": "application/json", "User-Agent": USER_AGENT}
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.load(response)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(2**attempt)
    raise RuntimeError(f"API request failed after {attempts} attempts: {url}") from last_error


def atomic_write(path: pathlib.Path, content: str) -> None:
    """Replace a file only when its content changed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = content.encode("utf-8")
    if path.exists() and path.read_bytes() == encoded:
        return
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(encoded)
    os.replace(temporary, path)


def search_page(
    api_url: str,
    page_size: int,
    start: int,
    filters: dict,
    sort_by: str = "relevance",
    sort: str = "desc",
) -> dict:
    query = urllib.parse.urlencode(
        {
            **filters,
            "limit": page_size,
            "start": start,
            "sort_by": sort_by,
            "sort": sort,
        }
    )
    return request_json(f"{api_url}/search/?{query}")


def fetch_partition(
    api_url: str,
    page_size: int,
    filters: dict,
    expected_count: int,
    sort_by: str,
    sort: str,
) -> list[dict]:
    records: list[dict] = []
    start = 0
    while start < expected_count:
        payload = search_page(
            api_url, page_size, start, filters, sort_by=sort_by, sort=sort
        )
        page = payload.get("data")
        if not isinstance(page, list):
            raise RuntimeError("Unexpected /search response: 'data' is not a list")
        if int(payload["count"]) != expected_count:
            raise RuntimeError("Catalog changed while it was being downloaded; retry later")
        records.extend(page)
        if not page:
            break
        start += len(page)
        print(f"Catalog: {len(records):,}/{expected_count:,}", file=sys.stderr)

    if len(records) != expected_count:
        raise RuntimeError(
            f"Incomplete partition {filters}: received {len(records)}, "
            f"expected {expected_count}"
        )
    return records


def fetch_unique_partition(
    api_url: str, page_size: int, filters: dict, expected_count: int
) -> list[dict]:
    """Recover a complete partition despite unstable ordering between API pages."""
    records_by_id: dict[str, dict] = {}
    sort_orders = [
        ("relevance", "desc"),
        ("relevance", "asc"),
        ("frequency", "desc"),
        ("frequency", "asc"),
        ("hits_90_days", "desc"),
        ("hits_90_days", "asc"),
    ]
    for sort_by, sort in sort_orders:
        records = fetch_partition(
            api_url, page_size, filters, expected_count, sort_by, sort
        )
        for item in records:
            series_id = item.get("field", {}).get("id")
            if not series_id:
                raise RuntimeError(f"Series without an ID in partition {filters}")
            records_by_id[series_id] = item
        print(
            f"Unique: {len(records_by_id):,}/{expected_count:,} "
            f"after {sort_by} {sort}",
            file=sys.stderr,
        )
        if len(records_by_id) == expected_count:
            return list(records_by_id.values())

    raise RuntimeError(
        f"Incomplete partition {filters}: recovered {len(records_by_id)} unique "
        f"series, expected {expected_count}"
    )


def fetch_category(
    api_url: str, page_size: int, theme: str, catalogs: list[str]
) -> list[dict]:
    theme_filters = {"dataset_theme": theme}
    total_count = int(search_page(api_url, 1, 0, theme_filters)["count"])
    if total_count <= 10_000:
        records = fetch_unique_partition(
            api_url, page_size, theme_filters, total_count
        )
    else:
        records = []
        partition_count = 0
        for catalog in catalogs:
            filters = {"catalog_id": catalog, "dataset_theme": theme}
            catalog_count = int(search_page(api_url, 1, 0, filters)["count"])
            if catalog_count:
                if catalog_count > 10_000:
                    raise RuntimeError(
                        f"Partition remains above API limit: {filters} ({catalog_count})"
                    )
                records.extend(
                    fetch_unique_partition(api_url, page_size, filters, catalog_count)
                )
                partition_count += catalog_count
        if partition_count != total_count:
            raise RuntimeError(
                f"Catalog partitions for {theme!r} contain {partition_count} records; "
                f"expected {total_count}"
            )

    ids = [item.get("field", {}).get("id") for item in records]
    if len(records) != total_count or len(set(ids)) != total_count or None in ids:
        raise RuntimeError(
            f"Incomplete category {theme!r}: received {len(records)} rows and "
            f"{len(set(ids))} unique IDs; expected {total_count}"
        )
    records.sort(key=lambda item: item.get("field", {}).get("id", ""))
    return records


def fetch_categories(
    api_url: str, page_size: int, categories: dict[str, str]
) -> dict[str, list[dict]]:
    catalogs = request_json(f"{api_url}/search/catalog_id/").get("data", [])
    available_themes = set(
        request_json(f"{api_url}/search/dataset_theme/").get("data", [])
    )
    if not catalogs or not available_themes:
        raise RuntimeError("The API returned an empty catalog or theme list")
    unknown = sorted(set(categories.values()) - available_themes)
    if unknown:
        raise RuntimeError(f"Unknown API theme(s): {', '.join(unknown)}")

    result = {}
    for filename, theme in categories.items():
        print(f"Category: {theme}", file=sys.stderr)
        result[filename] = fetch_category(api_url, page_size, theme, catalogs)
    return result


def catalog_csv(records: list[dict]) -> str:
    columns = [
        "series_id",
        "title",
        "description",
        "frequency",
        "time_index_start",
        "time_index_end",
        "units",
        "dataset_title",
        "publisher_name",
        "source",
        "theme",
    ]
    output = io.StringIO(newline="")
    writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
    writer.writeheader()
    for item in records:
        field = item.get("field", {})
        dataset = item.get("dataset", {})
        writer.writerow(
            {
                "series_id": field.get("id", ""),
                "title": field.get("title", ""),
                "description": field.get("description", ""),
                "frequency": field.get("frequency", ""),
                "time_index_start": field.get("time_index_start", ""),
                "time_index_end": field.get("time_index_end", ""),
                "units": field.get("units", ""),
                "dataset_title": dataset.get("title", ""),
                "publisher_name": dataset.get("publisher", {}).get("name", ""),
                "source": dataset.get("source", ""),
                "theme": dataset.get("theme", ""),
            }
        )
    return output.getvalue()


def configured_series(path: pathlib.Path) -> list[str]:
    if not path.exists():
        return []
    values = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if line and not line.startswith("#"):
            values.append(line)
    return sorted(set(values))


def fetch_series(api_url: str, series_id: str) -> dict:
    query = urllib.parse.urlencode(
        {"ids": series_id, "limit": 1000, "metadata": "full"}
    )
    return request_json(f"{api_url}/series/?{query}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--api-url", default=DEFAULT_API_URL)
    parser.add_argument("--output-dir", type=pathlib.Path, default=pathlib.Path("data"))
    parser.add_argument(
        "--series-file", type=pathlib.Path, default=pathlib.Path("config/series.txt")
    )
    parser.add_argument(
        "--categories-file",
        type=pathlib.Path,
        default=pathlib.Path("config/categories.json"),
    )
    parser.add_argument("--page-size", type=int, default=1000)
    args = parser.parse_args()

    api_url = args.api_url.rstrip("/")
    if not 1 <= args.page_size <= 1000:
        parser.error("--page-size must be between 1 and 1000")

    categories = json.loads(args.categories_file.read_text(encoding="utf-8"))
    if not isinstance(categories, dict) or not categories:
        raise RuntimeError("config/categories.json must contain a non-empty object")
    if any(
        not isinstance(filename, str)
        or not filename.replace("_", "").isalnum()
        or not isinstance(theme, str)
        for filename, theme in categories.items()
    ):
        raise RuntimeError("Category filenames and API themes must be simple strings")

    category_records = fetch_categories(api_url, args.page_size, categories)
    categories_dir = args.output_dir / "categories"
    categories_dir.mkdir(parents=True, exist_ok=True)
    expected_category_files = {f"{filename}.csv" for filename in categories}
    for path in categories_dir.glob("*.csv"):
        if path.name not in expected_category_files:
            path.unlink()
    for filename, records in category_records.items():
        atomic_write(categories_dir / f"{filename}.csv", catalog_csv(records))

    ids = configured_series(args.series_file)
    known_ids = {
        item.get("field", {}).get("id")
        for records in category_records.values()
        for item in records
    }
    unknown = [series_id for series_id in ids if series_id not in known_ids]
    if unknown:
        raise RuntimeError(f"Unknown series ID(s): {', '.join(unknown)}")

    series_dir = args.output_dir / "series"
    if series_dir.exists():
        expected_files = {f"{series_id}.json" for series_id in ids}
        for path in series_dir.glob("*.json"):
            if path.name not in expected_files:
                path.unlink()

    for series_id in ids:
        print(f"Series: {series_id}", file=sys.stderr)
        payload = fetch_series(api_url, series_id)
        atomic_write(
            series_dir / f"{series_id}.json",
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )

    total_rows = sum(len(records) for records in category_records.values())
    print(
        f"Updated {len(categories)} category CSVs ({total_rows:,} rows) "
        f"and {len(ids)} selected series"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
