import re
import requests


def to_usd(price_string):
    rates = {k: 1 / v for k, v in requests.get(
        "https://open.er-api.com/v6/latest/USD").json()["rates"].items()}
    symbol_map = {'$': 'USD', '€': 'EUR', '£': 'GBP', '₹': 'INR'}
    pattern = r'([\$€£₹])?\s?([\d,]+(?:\.\d{2})?)\s?(USD|EUR|GBP|INR)?'
    match = re.search(pattern, str(price_string))

    if not match:
        return None

    amount = float(match.group(2).replace(',', ''))
    symbol = match.group(1)
    code = match.group(3)
    currency = symbol_map.get(symbol, code)

    return round(amount * rates.get(currency, 1), 2)


def extract_numeric_value(series):
    return series.str.extract(r"(\d+)")[0].fillna(0).astype(int)


def extract_antutu_score(bench_series):
    return bench_series.str.extract(r"AnTuTu:\s*(\d+)")[0].fillna(0).astype(int)


def extract_display_type(display_series):
    return (display_series.str.strip()
            .str.split(",")
            .apply(lambda x: ", ".join(i.strip() for i in x) if isinstance(x, list) else x)
            .str.split(",")
            .str[0]
            .str.strip())


def extract_brightness(specs):
    from_tests = specs["tests"]["Display"].str.extract(r"(\d+)\s*nits")[0]
    from_display = specs["display"]["displaytype"].str.extract(
        r"(\d+)\s*nits")[0]
    return from_tests.combine_first(from_display).astype("Int64")


def extract_chipset_info(chipset_series):
    return chipset_series.apply(
        lambda x: ", ".join(i.split(" (")[0].strip() for i in x) if isinstance(x, list)
        else x.split(" (")[0].strip() if isinstance(x, str) else x
    )
