"""
YGOPRODeck API client.
Public API — no authentication required.
Rate limit: 20 requests/second (we stay well under this).
"""
import time
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

API_BASE = getattr(settings, 'YGOPRODECK_API_BASE', 'https://db.ygoprodeck.com/api/v7')
DELAY = getattr(settings, 'YGOPRODECK_RATE_LIMIT_DELAY', 1.0)

HEADERS = {
    'User-Agent': 'YugiohPriceRankingApp/1.0 (educational project; see README)',
    'Accept': 'application/json',
}


def _get(endpoint: str, params: dict = None) -> dict | None:
    """Make a rate-limited GET request to the YGOPRODeck API."""
    url = f'{API_BASE}/{endpoint}'
    try:
        time.sleep(DELAY)
        resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
        if resp.status_code == 200:
            return resp.json()
        elif resp.status_code == 404:
            logger.warning('YGOPRODeck 404: %s params=%s', url, params)
            return None
        else:
            logger.error('YGOPRODeck error %s: %s', resp.status_code, url)
            return None
    except requests.RequestException as e:
        logger.error('YGOPRODeck request failed: %s', e)
        return None


def fetch_card_by_name(name: str) -> dict | None:
    """
    Fetch a single card by exact name from the API.
    Returns the raw card dict or None if not found.
    """
    data = _get('cardinfo.php', {'name': name, 'misc': 'yes'})
    if data and 'data' in data and data['data']:
        return data['data'][0]
    return None


def fetch_card_by_id(card_id: int) -> dict | None:
    """Fetch a single card by its passcode/ID."""
    data = _get('cardinfo.php', {'id': card_id, 'misc': 'yes'})
    if data and 'data' in data and data['data']:
        return data['data'][0]
    return None


def fetch_card_ja_by_id(card_id: int) -> dict | None:
    """Fetch Japanese card data (name, desc, set names) from the API."""
    data = _get('cardinfo.php', {'id': card_id, 'language': 'ja', 'misc': 'yes'})
    if data and 'data' in data and data['data']:
        return data['data'][0]
    return None


def fetch_card_ja_by_name(name: str) -> dict | None:
    """Fetch Japanese card data by English name."""
    data = _get('cardinfo.php', {'name': name, 'language': 'ja', 'misc': 'yes'})
    if data and 'data' in data and data['data']:
        return data['data'][0]
    return None


def search_cards_by_name(fname: str) -> list[dict]:
    """
    Fuzzy-name search. Returns list of card dicts (may be multiple).
    """
    data = _get('cardinfo.php', {'fname': fname, 'misc': 'yes'})
    if data and 'data' in data:
        return data['data']
    return []


def search_cards_ja_by_name(fname: str) -> list[dict]:
    """
    Fuzzy-name search for Japanese names.
    Returns list of Japanese card dicts.
    """
    data = _get('cardinfo.php', {'fname': fname, 'language': 'ja', 'misc': 'yes'})
    if data and 'data' in data:
        return data['data']
    return []


def fetch_all_cards(offset: int = 0, num: int = 100) -> list[dict]:
    """
    Fetch a paginated batch of all cards.
    Used for the initial price-update scan.
    """
    data = _get('cardinfo.php', {'num': num, 'offset': offset, 'misc': 'yes'})
    if data and 'data' in data:
        return data['data']
    return []
