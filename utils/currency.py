import json
import time
from urllib.request import urlopen, Request

# Simple in-memory caches
_country_currency_map = None
_rates_cache = {}


def _fetch_countries():
    global _country_currency_map
    if _country_currency_map is not None:
        return _country_currency_map
    url = "https://restcountries.com/v3.1/all?fields=name,currencies"
    req = Request(url, headers={"User-Agent": "ExpenseMgmt/1.0"})
    with urlopen(req, timeout=10) as resp:
        data = json.load(resp)
    mapping = {}
    for c in data:
        name = None
        try:
            name = c.get('name', {}).get('common')
        except Exception:
            continue
        currencies = c.get('currencies') or {}
        # pick first currency code if available
        code = None
        if isinstance(currencies, dict) and len(currencies) > 0:
            try:
                code = list(currencies.keys())[0]
            except Exception:
                code = None
        if name and code:
            mapping[name] = code
    _country_currency_map = mapping
    return _country_currency_map


def get_all_countries():
    mapping = _fetch_countries()
    # return sorted list of country names
    return sorted(mapping.keys())


def get_currency_for_country(country_name: str):
    """Return a 3-letter currency code (e.g., 'USD') for the given country name.

    This queries restcountries and caches the mapping in memory.
    """
    if not country_name:
        return None
    mapping = _fetch_countries()
    # try exact match
    if country_name in mapping:
        return mapping[country_name]
    # try case-insensitive match
    for k, v in mapping.items():
        if k.lower() == country_name.lower():
            return v
    # no match
    return None


def _fetch_rates(base: str):
    # cache for 10 minutes per base
    now = time.time()
    entry = _rates_cache.get(base)
    if entry and now - entry['ts'] < 600:
        return entry['rates']
    url = f"https://api.exchangerate-api.com/v4/latest/{base}"
    req = Request(url, headers={"User-Agent": "ExpenseMgmt/1.0"})
    try:
        with urlopen(req, timeout=10) as resp:
            data = json.load(resp)
    except Exception:
        return None
    rates = data.get('rates')
    if rates:
        _rates_cache[base] = {'ts': now, 'rates': rates}
    return rates


def convert_amount(amount: float, from_currency: str, to_currency: str):
    """Convert amount from `from_currency` to `to_currency` using exchangerate-api.

    Returns float or None if conversion failed.
    """
    if amount is None:
        return None
    if not from_currency or not to_currency:
        return None
    if from_currency.upper() == to_currency.upper():
        return float(amount)
    # Fetch rates with base=from_currency so rates[to_currency] gives multiplier
    rates = _fetch_rates(from_currency.upper())
    if not rates:
        return None
    rate = rates.get(to_currency.upper())
    if rate is None:
        return None
    try:
        return float(amount) * float(rate)
    except Exception:
        return None
