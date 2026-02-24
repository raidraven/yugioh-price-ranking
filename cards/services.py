"""
Service layer for syncing card data from YGOPRODeck API into the local DB.
"""
import logging
from decimal import Decimal, InvalidOperation
from django.utils import timezone
from .models import Card, CardSet, CardArtwork
from . import api_client, rakuten_api

logger = logging.getLogger(__name__)


def _safe_decimal(value) -> Decimal | None:
    """Convert a string/number to Decimal, returning None on failure."""
    try:
        if value is None or value == '0.00' or value == '0':
            return None
        d = Decimal(str(value))
        return d if d > 0 else None
    except (InvalidOperation, ValueError):
        return None


def sync_card_from_api_data(api_data: dict) -> Card | None:
    """
    Given raw API response data for one card, upsert Card + CardSet rows.
    Returns the Card instance or None on error.
    """
    if not api_data:
        return None

    card_id = api_data.get('id')
    if not card_id:
        return None

    # Extract image info
    images = api_data.get('card_images', [])
    image_url = images[0].get('image_url', '') if images else ''
    image_url_small = images[0].get('image_url_small', '') if images else ''
    image_url_cropped = images[0].get('image_url_cropped', '') if images else ''

    # Extract misc info
    misc_info = api_data.get('misc_info', [{}])
    konami_id = misc_info[0].get('konami_id') if misc_info else None

    card, created = Card.objects.update_or_create(
        card_id=card_id,
        defaults={
            'name': api_data.get('name', ''),
            'card_type': api_data.get('type', ''),
            'frame_type': api_data.get('frameType', ''),
            'description': api_data.get('desc', ''),
            'atk': api_data.get('atk'),
            'def_points': api_data.get('def'),
            'level': api_data.get('level'),
            'scale': api_data.get('scale'),
            'linkval': api_data.get('linkval'),
            'linkmarkers': ','.join(api_data.get('linkmarkers', [])),
            'race': api_data.get('race', ''),
            'attribute': api_data.get('attribute', ''),
            'archetype': api_data.get('archetype', ''),
            'image_url': image_url,
            'image_url_small': image_url_small,
            'image_url_cropped': image_url_cropped,
            'konami_id': konami_id,
            'api_url': api_data.get('ygoprodeck_url', ''),
        }
    )
    action = 'Created' if created else 'Updated'
    logger.info('%s card: %s (ID=%s)', action, card.name, card.card_id)

    # Sync all artwork images (card_images array from API)
    for idx, img in enumerate(images):
        img_id = img.get('id')
        if not img_id:
            continue
        CardArtwork.objects.update_or_create(
            card=card,
            artwork_index=idx,
            defaults={
                'image_id': img_id,
                'image_url': img.get('image_url', ''),
                'image_url_small': img.get('image_url_small', ''),
                'image_url_cropped': img.get('image_url_cropped', ''),
            }
        )

    # Sync card sets and prices
    raw_prices = api_data.get('card_prices', [{}])
    price_dict = raw_prices[0] if raw_prices else {}

    for raw_set in api_data.get('card_sets', []):
        set_code = raw_set.get('set_code', '')
        if not set_code:
            continue
        cs, _ = CardSet.objects.update_or_create(
            card=card,
            set_code=set_code,
            defaults={
                'set_name': raw_set.get('set_name', ''),
                'set_rarity': raw_set.get('set_rarity', ''),
                'set_rarity_code': raw_set.get('set_rarity_code', ''),
                # Card-level prices (lowest across all printings)
                'cardmarket_price': _safe_decimal(price_dict.get('cardmarket_price')),
                'tcgplayer_price': _safe_decimal(price_dict.get('tcgplayer_price')),
                'ebay_price': _safe_decimal(price_dict.get('ebay_price')),
                'amazon_price': _safe_decimal(price_dict.get('amazon_price')),
                'coolstuffinc_price': _safe_decimal(price_dict.get('coolstuffinc_price')),
            }
        )
        cs.compute_min_price()
        cs.save()

    # If no sets returned, ensure at least one CardSet exists for price display
    if not api_data.get('card_sets'):
        cs, _ = CardSet.objects.update_or_create(
            card=card,
            set_code='UNKNOWN',
            defaults={
                'set_name': '不明',
                'set_rarity': '不明',
                'set_rarity_code': '',
                'cardmarket_price': _safe_decimal(price_dict.get('cardmarket_price')),
                'tcgplayer_price': _safe_decimal(price_dict.get('tcgplayer_price')),
                'ebay_price': _safe_decimal(price_dict.get('ebay_price')),
                'amazon_price': _safe_decimal(price_dict.get('amazon_price')),
                'coolstuffinc_price': _safe_decimal(price_dict.get('coolstuffinc_price')),
            }
        )
        cs.compute_min_price()
        cs.save()

    return card


def sync_ja_data(card: 'Card', ja_data: dict) -> None:
    """
    Sync Japanese name, description, and set names from the ?language=ja API response.
    Updates card.name_ja, card.description_ja, and CardSet.set_name_ja.
    """
    if not ja_data:
        return

    # Update Japanese name and description on Card
    name_ja = ja_data.get('name', '')
    desc_ja = ja_data.get('desc', '')
    if name_ja or desc_ja:
        Card.objects.filter(pk=card.pk).update(
            name_ja=name_ja or card.name_ja,
            description_ja=desc_ja or card.description_ja,
        )
        card.name_ja = name_ja or card.name_ja
        card.description_ja = desc_ja or card.description_ja

    # 楽天の最安値を取得して更新 (日本語名が存在する場合)
    if card.name_ja:
        rakuten_price, rakuten_url = rakuten_api.fetch_min_price(card.name_ja)
        if rakuten_price is not None:
            Card.objects.filter(pk=card.pk).update(
                rakuten_min_price=rakuten_price,
                rakuten_affiliate_url=rakuten_url
            )
            card.rakuten_min_price = rakuten_price
            card.rakuten_affiliate_url = rakuten_url

    # Update Japanese set names where available from API (often empty or English)
    for raw_set in ja_data.get('card_sets', []):
        set_code = raw_set.get('set_code', '')
        set_name_ja = raw_set.get('set_name', '')
        
        # API often returns English set names even for ?language=ja
        # We only save it if it contains actual Japanese characters
        is_english = sum(1 for c in set_name_ja if c.isascii() and c.isalpha()) > len(set_name_ja) * 0.5
        
        if set_code and set_name_ja and not is_english:
            CardSet.objects.filter(card=card, set_code=set_code).update(
                set_name_ja=set_name_ja
            )

    # Scrape real OCG set names from Yugioh Wiki
    try:
        from .wiki_scraper import apply_wiki_sets_to_card
        apply_wiki_sets_to_card(card)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Failed to apply wiki sets for {card.name}: {e}")


def get_or_fetch_card(name: str) -> Card | None:
    """
    Search DB first; if not found, fetch EN+JA from API and store.
    Used by the search view for on-demand stocking.
    """
    # Check DB first (case-insensitive)
    existing = Card.objects.filter(name__iexact=name).first()
    if existing:
        return existing

    api_data = api_client.fetch_card_by_name(name)
    if not api_data:
        return None
    card = sync_card_from_api_data(api_data)
    if card:
        # Also fetch Japanese data
        ja_data = api_client.fetch_card_ja_by_id(card.card_id)
        sync_ja_data(card, ja_data)
    return card


def update_all_prices(max_cards: int = 500) -> int:
    """
    Refresh prices for all cards in the DB from the API.
    Called by the APScheduler job every morning at 7:00 JST.
    Returns number of cards updated.
    """
    cards = Card.objects.all()[:max_cards]
    updated = 0
    for card in cards:
        api_data = api_client.fetch_card_by_id(card.card_id)
        if api_data:
            synced_card = sync_card_from_api_data(api_data)
            # 日本語データと楽天価格の更新も行う
            ja_data = api_client.fetch_card_ja_by_id(card.card_id)
            sync_ja_data(synced_card, ja_data)
            updated += 1
        else:
            # Mark all sets as price-unavailable
            card.card_sets.update(
                price_available=False,
                price_updated_at=timezone.now()
            )
    logger.info('Price update complete: %d cards updated', updated)
    return updated
