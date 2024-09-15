import logging
from time import time
from poe_profit_calc.items import ITEM_NAMES, Item, PoeNinjaSource
from poe_profit_calc.fetcher import Fetcher, FetchError, Format
from poe_profit_calc.sourcemappings import ENDPOINT_MAPPING
from itertools import groupby


class Pricer:
    def __init__(
        self,
        fetcher: Fetcher,
        source_mapping: dict[PoeNinjaSource, str],
        cache_time_seconds=1800,
    ):
        self.fetcher = fetcher
        self.source_mapping = source_mapping
        self.cache_time_seconds = cache_time_seconds
        self.item_last_fetch: dict[Item, float] = {}

    def price_items(self, items: set[Item]) -> None:
        t = time()
        items_to_fetch = set()
        for item in items:
            if item not in self.item_last_fetch:
                items_to_fetch.add(item)
                self.item_last_fetch[item] = t
            elif abs(self.item_last_fetch[item] - t) > self.cache_time_seconds:
                items_to_fetch.add(item)
                self.item_last_fetch[item] = t
        fetch_and_price(items_to_fetch, self.fetcher, self.source_mapping)

    def get_raw_endpoint(self, source: PoeNinjaSource, format: Format = Format.JSON) -> bytes:
        return self.fetcher.fetch_data(self.source_mapping[source], Format.BYTES)


def fetch_and_price(items: set[Item], fetcher: Fetcher, source_mapping) -> None:
    groups = group_by_source(items, source_mapping)

    for data_source, item_group in groups.items():
        try:
            data = fetcher.fetch_data(data_source)
        except FetchError as e:
            logging.warning(f"Failed to fetch data from {data_source} with message: {str(e)}")
            data = {}
        extract_prices(data, item_group)


def group_by_source(
    items: set[Item], source_mapping: dict[PoeNinjaSource, str]
) -> dict[str, set[Item]]:
    groups = {}
    for item in items:
        source = source_mapping[item.matcher.source]
        if source not in groups:
            groups[source] = {item}
        else:
            groups[source].add(item)
    return groups


def extract_prices(data, items: set[Item]) -> None:
    unprocessed_items = items.copy()
    for item_data in data.get("lines", {}):
        if not unprocessed_items:
            break
        if item_data.get("name", item_data.get("currencyTypeName")) not in ITEM_NAMES:
            continue
        to_remove = set()
        for item in unprocessed_items:
            if item.match(item_data):
                to_remove.add(item)
        unprocessed_items.difference_update(to_remove)
    currency_details = data.get("currencyDetails", {})
    if currency_details:
        extract_currency_imgs(items, currency_details)


def extract_currency_imgs(items: set[Item], currency_details: dict) -> None:
    unprocessed_items = items.copy()
    for currency_detail in currency_details:
        if not unprocessed_items:
            break
        to_remove = set()
        for item in items:
            if item.match_currency_details(currency_detail):
                to_remove.add(item)
        unprocessed_items.difference_update(to_remove)
