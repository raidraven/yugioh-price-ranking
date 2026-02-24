import re
import logging
import urllib.request
import urllib.parse
from django.utils.timezone import now
from .models import Card, CardSet

logger = logging.getLogger(__name__)

def get_wiki_sets(card_name: str) -> list[str]:
    """
    Scrape '収録パック等' (set names) from yugioh-wiki.net for a given card name.
    Returns a list of raw set name strings from the wiki.
    """
    if not card_name:
        return []
    
    from .utils import to_full_width_for_wiki
    card_name_fw = to_full_width_for_wiki(card_name)

    # Wiki URL encoding: EUC-JP bytes in URL, format is 《Card Name》
    try:
        encoded_name = card_name_fw.encode('euc-jp', errors='ignore')
        brackets = '《'.encode('euc-jp') + encoded_name + '》'.encode('euc-jp')
        query = urllib.parse.quote(brackets)
        url = f'https://yugioh-wiki.net/index.php?{query}'
    except Exception as e:
        logger.error(f"Wiki encoding error for {card_name}: {e}")
        return []

    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (YugiohPriceApp)'})
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('euc-jp', errors='ignore')
            
            # Many pages do not have id="pack", but they always have "収録パック等"
            idx = html.find('収録パック等')
            if idx == -1: 
                return []
            
            ul_idx = html.find('<ul', idx)
            if ul_idx == -1: 
                return []
            
            ul_end = html.find('</ul>', ul_idx)
            if ul_end == -1: 
                return []
            
            ul_chunk = html[ul_idx:ul_end]
            items = re.findall(r'<li>(.*?)</li>', ul_chunk, re.DOTALL)
            
            clean_items = []
            for i in items:
                # Strip all HTML tags
                clean = re.sub(r'<[^>]+>', '', i)
                clean_items.append(clean.strip())
            return clean_items
    except Exception as e:
        logger.warning(f"Wiki scrape failed for {card_name}: {e}")
        return []

def get_wiki_description(card_name: str) -> str:
    """
    Scrape the full Japanese card text (including Pendulum effects) from yugioh-wiki.net.
    """
    if not card_name:
        return ""
    from .utils import to_full_width_for_wiki
    card_name_fw = to_full_width_for_wiki(card_name)
    
    try:
        encoded_name = card_name_fw.encode('euc-jp', errors='ignore')
        brackets = '《'.encode('euc-jp') + encoded_name + '》'.encode('euc-jp')
        query = urllib.parse.quote(brackets)
        url = f'https://yugioh-wiki.net/index.php?{query}'
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (YugiohPriceApp)'})
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('euc-jp', errors='ignore')
            m = re.search(r'<pre>(.*?)</pre>', html, re.DOTALL)
            if m:
                text = m.group(1).strip()
                text = re.sub(r'<[^>]+>', '', text)
                return text
    except Exception as e:
        logger.warning(f"Wiki description scrape failed for {card_name}: {e}")
    return ""

def apply_wiki_sets_to_card(card: Card) -> bool:
    """
    Fetch wiki data and try to match it against local CardSets via Set Codes.
    Returns True if any updates were made.
    """
    if not card.name_ja:
        return False

    raw_sets = get_wiki_sets(card.name_ja)
    wiki_desc = get_wiki_description(card.name_ja)
    
    updates_made = False

    # 1. Update description_ja if wiki description is present and different.
    # We no longer strictly check for specific characters to allow Normal Monsters.
    if wiki_desc and card.description_ja != wiki_desc:
        Card.objects.filter(pk=card.pk).update(description_ja=wiki_desc)
        card.description_ja = wiki_desc
        updates_made = True

    if not raw_sets:
        return updates_made
        
    # YGOPRODeck only provides TCG sets (e.g. LOB-001) even for language=ja.
    # Yu-Gi-Oh Wiki provides OCG sets (e.g. EX-06, PHNI-JP001).
    # Since codes rarely match, we create distinct CardSet records for the Japanese OCG sets.
    
    # Optional: Clear previously scraped Wiki OCG sets for this card (to prevent duplicates if wiki updates)
    # A Wiki OCG set is characterized by having no prices and no English set_name.
    # To be safe, we'll just use get_or_create by checking set_name_ja and set_code.
    
    for raw in raw_sets:
        parts = raw.split()
        if len(parts) >= 2:
            if re.match(r'^[A-Z0-9]+-[A-Z0-9]+$', parts[-2]):
                code = parts[-2]
                name = ' '.join(parts[:-2])
                rarity = parts[-1]
            else:
                code = ''
                name = ' '.join(parts[:-1])
                rarity = parts[-1]
        else:
            name = raw
            code = ''
            rarity = ''
            
        # Clean up any trailing English names embedded in the wiki name
        name = re.sub(r'[\-－]+[A-Za-z0-9\s\'\,\.]+[\-－]*\s*$', '', name).strip()
        
        # If the set has no code (early OCG like Vol.1), use the name as the dummy code
        # This prevents IntegrityError on `unique_together = ('card', 'set_code')`
        if not code:
            code = name
        
        if name:
            obj, created = CardSet.objects.update_or_create(
                card=card,
                set_code=code,
                defaults={
                    'set_name_ja': name,
                    'set_name': name,
                    'set_rarity': rarity,
                }
            )
            if created:
                obj.price_available = False
                obj.save()
                updates_made = True

    return updates_made
