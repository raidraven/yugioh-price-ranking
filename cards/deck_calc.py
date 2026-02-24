"""
Deck Price Calculator helpers.
Handles: OCR image -> card list, text parsing, YDKE URL decoding, price lookup.
"""
import re
import base64
import struct
import logging
import statistics
from collections import Counter
from decimal import Decimal

logger = logging.getLogger(__name__)


# ── Text Parsing ─────────────────────────────────────────────────────────────

def parse_text_deck(text: str) -> list[tuple[str, int]]:
    """
    Parse a deck text block into list of (card_name, count).
    Supports formats:
      "3 ブラック・マジシャン"
      "ブラック・マジシャン x3"
      "ブラック・マジシャン ×3"
      "ブラック・マジシャン"  ← count defaults to 1
      Lines starting with # or // are ignored.
    """
    result = []
    seen = {}  # name -> accumulated count (deduplicate OCR repetitions)
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('//'):
            continue
        # Strip common noise characters from OCR output
        line = re.sub(r'[|｜_\-=]+$', '', line).strip()
        if len(line) < 2:
            continue

        count = 1
        name = line

        # "3 CardName" or "3x CardName" or "3× CardName"
        m = re.match(r'^(\d+)\s*[xX×]?\s+(.+)$', line)
        if m:
            count = min(int(m.group(1)), 3)
            name = m.group(2).strip()
        else:
            # "CardName x3" or "CardName ×3" or "CardName X3"
            m = re.match(r'^(.+?)\s+[xX×](\d+)\s*$', line)
            if m:
                name = m.group(1).strip()
                count = min(int(m.group(2)), 3)

        if name and len(name) >= 2:
            if name in seen:
                seen[name] = min(seen[name] + count, 3)
            else:
                seen[name] = count

    return list(seen.items())


# ── YDKE Decoding ────────────────────────────────────────────────────────────

def decode_ydke(url: str) -> Counter:
    """
    Decode YDKE URL to Counter of {card_id: copies}.
    YDKE format: ydke://[main base64]![extra base64]![side base64]
    """
    try:
        url = url.strip()
        if not url.lower().startswith('ydke://'):
            return Counter()

        content = url[7:]  # Strip "ydke://"
        parts = content.split('!')

        all_ids: list[int] = []
        for part in parts[:3]:  # main / extra / side
            if not part:
                continue
            # Fix base64 padding
            padding = 4 - len(part) % 4
            if padding < 4:
                part += '=' * padding
            try:
                decoded = base64.b64decode(part)
                ids = [
                    struct.unpack_from('<I', decoded, j)[0]
                    for j in range(0, len(decoded), 4)
                    if j + 4 <= len(decoded)
                ]
                all_ids.extend(ids)
            except Exception as e:
                logger.warning('YDKE section decode error: %s', e)
                continue

        return Counter(all_ids)
    except Exception as e:
        logger.warning('YDKE decode error: %s', e)
        return Counter()


# ── OCR Image Processing ─────────────────────────────────────────────────────

def ocr_image(image_file) -> tuple[str | None, str | None]:
    """
    Run OCR on an uploaded image file.
    Returns (extracted_text, error_message).
    error_message is None on success.
    """
    try:
        import pytesseract
        from PIL import Image, ImageEnhance, ImageOps, ImageFilter
    except ImportError:
        return None, (
            'pytesseract または Pillow がインストールされていません。'
            'テキスト入力または YDKE リンクをご利用ください。'
        )

    try:
        img = Image.open(image_file)

        # Normalise mode
        if img.mode in ('RGBA', 'P', 'LA'):
            img = img.convert('RGB')

        # Scale up small images for better OCR accuracy
        w, h = img.size
        if w < 800:
            factor = 800 / w
            img = img.resize((int(w * factor), int(h * factor)), Image.LANCZOS)

        # Greyscale
        gray = img.convert('L')

        # Detect if background is dark (Master Duel / YGOPRO screenshots)
        sample = list(gray.getdata())[::200]
        avg = statistics.mean(sample) if sample else 128
        if avg < 128:
            gray = ImageOps.invert(gray)

        # Enhance contrast then sharpen
        gray = ImageEnhance.Contrast(gray).enhance(2.0)
        gray = gray.filter(ImageFilter.SHARPEN)

        # OCR: Japanese + English
        try:
            text = pytesseract.image_to_string(
                gray, lang='jpn+eng', config='--psm 6 --oem 3'
            )
        except pytesseract.pytesseract.TesseractError:
            # Japanese lang pack not installed; English only
            try:
                text = pytesseract.image_to_string(
                    gray, lang='eng', config='--psm 6 --oem 3'
                )
            except Exception as e:
                return None, f'OCR エラー: {e}'

        return text.strip(), None

    except pytesseract.pytesseract.TesseractNotFoundError:
        return None, (
            'Tesseract OCR がインストールされていません。\n'
            'Windows: https://github.com/UB-Mannheim/tesseract/wiki からインストールしてください。\n'
            'または、テキスト入力または YDKE リンクをご利用ください。'
        )
    except Exception as e:
        logger.exception('OCR unexpected error')
        return None, f'画像の処理に失敗しました: {e}'


# ── Card Lookup & Price Calculation ──────────────────────────────────────────

def _get_best_set(card):
    """Return lowest-price CardSet for a card, or any set if no price."""
    cs = (
        card.card_sets.filter(price_available=True, min_price__isnull=False, min_price__gt=0)
        .order_by('min_price')
        .first()
    )
    return cs or card.card_sets.first()


def _jpy(card, best_set) -> tuple[int, bool]:
    """
    Convert to JPY integer. Returns (price, is_rakuten).
    Prefers Card.rakuten_min_price if available.
    """
    if card and card.rakuten_min_price is not None and card.rakuten_min_price > 0:
        return card.rakuten_min_price, True

    if not best_set or not best_set.min_price:
        return 0, False
        
    from django.conf import settings
    usd_rate = getattr(settings, 'USD_TO_JPY_RATE', 150)
    eur_rate = getattr(settings, 'EUR_TO_JPY_RATE', 160)
    rate = eur_rate if best_set.min_price_source == 'Cardmarket' else usd_rate
    return round(float(best_set.min_price) * rate), False


def _find_card_by_name(name: str):
    """Look up Card by Japanese or English name, falling back to API fuzzy search."""
    from .models import Card
    from . import api_client, services

    # 1. Exact Japanese name
    card = Card.objects.filter(name_ja=name).first()
    if card:
        return card
    # 2. Exact English (case-insensitive)
    card = Card.objects.filter(name__iexact=name).first()
    if card:
        return card
    # 3. Partial Japanese
    card = Card.objects.filter(name_ja__icontains=name).first()
    if card:
        return card
    # 4. Partial English
    card = Card.objects.filter(name__icontains=name).first()
    if card:
        return card
    # 5. API fuzzy search (fname= parameter)
    results = api_client.search_cards_by_name(name)
    if results:
        card = services.sync_card_from_api_data(results[0])
        # Also fetch Japanese data
        if card:
            ja = api_client.fetch_card_ja_by_id(card.card_id)
            services.sync_ja_data(card, ja)
        return card
    return None


def lookup_cards_from_names(card_list: list[tuple[str, int]]) -> tuple[list, list]:
    """
    Look up cards by name list.
    Returns (results, not_found).
    results: list of dicts with card/count/best_set/price_jpy/subtotal_jpy.
    not_found: list of unmatched name strings.
    """
    results = []
    not_found = []
    for name, count in card_list:
        card = _find_card_by_name(name)
        if card:
            best = _get_best_set(card)
            price, is_rakuten = _jpy(card, best)
            results.append({
                'card': card,
                'count': count,
                'best_set': best,
                'price_jpy': price,
                'subtotal_jpy': price * count,
                'is_rakuten': is_rakuten,
            })
        else:
            not_found.append(name)
    return results, not_found


def lookup_cards_from_ids(id_counter: Counter) -> tuple[list, list]:
    """
    Look up cards by YDKE card_id Counter.
    Returns (results, not_found).
    """
    from .models import Card
    from . import api_client, services

    results = []
    not_found = []
    for card_id, count in id_counter.items():
        card = Card.objects.filter(card_id=card_id).first()
        if not card:
            data = api_client.fetch_card_by_id(card_id)
            if data:
                card = services.sync_card_from_api_data(data)
        if card:
            best = _get_best_set(card)
            price, is_rakuten = _jpy(card, best)
            results.append({
                'card': card,
                'count': count,
                'best_set': best,
                'price_jpy': price,
                'subtotal_jpy': price * count,
                'is_rakuten': is_rakuten,
            })
        else:
            not_found.append(f'ID:{card_id}')
    return results, not_found
