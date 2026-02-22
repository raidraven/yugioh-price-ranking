"""
Custom Django template filters for Yu-Gi-Oh localization (Japanese).
Usage: {% load yugioh_filters %} in templates.
"""
from django import template
from django.conf import settings

register = template.Library()

# ── Card type translations ─────────────────────────────────────────────
CARD_TYPE_JA = {
    'normal monster':                    '通常モンスター',
    'effect monster':                    '効果モンスター',
    'fusion monster':                    '融合モンスター',
    'ritual monster':                    '儀式モンスター',
    'synchro monster':                   'シンクロモンスター',
    'xyz monster':                       'エクシーズモンスター',
    'link monster':                      'リンクモンスター',
    'pendulum effect monster':           'ペンデュラム効果モンスター',
    'pendulum normal monster':           'ペンデュラム通常モンスター',
    'pendulum fusion monster':           'ペンデュラム融合モンスター',
    'pendulum synchro monster':          'ペンデュラムシンクロモンスター',
    'pendulum xyz monster':              'ペンデュラムエクシーズモンスター',
    'synchro pendulum effect monster':   'シンクロペンデュラム効果モンスター',
    'xyz pendulum effect monster':       'エクシーズペンデュラム効果モンスター',
    'ritual effect monster':             '儀式効果モンスター',
    'spell card':                        '魔法カード',
    'trap card':                         '罠カード',
    'token':                             'トークン',
    'skill card':                        'スキルカード',
}

# ── Attribute translations ─────────────────────────────────────────────
ATTRIBUTE_JA = {
    'dark':   '闇',
    'light':  '光',
    'fire':   '炎',
    'water':  '水',
    'wind':   '風',
    'earth':  '地',
    'divine': '神',
}

# ── Race/Type translations ─────────────────────────────────────────────
RACE_JA = {
    'spellcaster':  '魔法使い族',
    'warrior':      '戦士族',
    'dragon':       'ドラゴン族',
    'fiend':        '悪魔族',
    'zombie':       'アンデット族',
    'machine':      '機械族',
    'aqua':         '水族',
    'pyro':         '炎族',
    'thunder':      '雷族',
    'rock':         '岩石族',
    'winged beast': '鳥獣族',
    'plant':        '植物族',
    'insect':       '昆虫族',
    'beast':        '獣族',
    'beast-warrior':'獣戦士族',
    'dinosaur':     '恐竜族',
    'sea serpent':  '海竜族',
    'reptile':      '爬虫類族',
    'fish':         '魚族',
    'psychic':      '念動力族',
    'divine-beast': '幻神獣族',
    'creator-god':  '創造神族',
    'cyberse':      'サイバース族',
    'wyrm':         '幻竜族',
    'fairy':        '天使族',
    # Spell/Trap sub-types
    'normal':       '通常',
    'equip':        '装備',
    'field':        'フィールド',
    'quick-play':   '速攻',
    'ritual':       '儀式',
    'continuous':   '永続',
    'counter':      'カウンター',
}

# ── Rarity translations ────────────────────────────────────────────────
RARITY_JA = {
    'common':                          'ノーマル',
    'rare':                            'レア',
    'super rare':                      'スーパーレア',
    'ultra rare':                      'ウルトラレア',
    'secret rare':                     'シークレットレア',
    'ultimate rare':                   'アルティメットレア',
    'ghost rare':                      'ゴーストレア',
    'starlight rare':                  'スターライトレア',
    "collector's rare":                'コレクターズレア',
    'gold rare':                       'ゴールドレア',
    'platinum rare':                   'プラチナレア',
    'prismatic secret rare':           'プリズマティックシークレットレア',
    'quarter century secret rare':     'クォーターセンチュリーシークレットレア',
    'premium gold rare':               'プレミアムゴールドレア',
    'short print':                     'ショートプリント',
    'super short print':               'スーパーショートプリント',
}

# ── Price source translations ──────────────────────────────────────────
SOURCE_JA = {
    'TCGPlayer':    'TCGプレイヤー',
    'Cardmarket':   'カードマーケット',
    'eBay':         'イーベイ',
    'Amazon':       'アマゾン',
    'CoolStuffInc': 'クールスタッフ',
}


@register.filter(name='card_type_ja')
def card_type_ja(value):
    """Translate card type to Japanese."""
    return CARD_TYPE_JA.get(str(value).lower(), value)


@register.filter(name='attribute_ja')
def attribute_ja(value):
    """Translate attribute to Japanese."""
    return ATTRIBUTE_JA.get(str(value).lower(), value)


@register.filter(name='race_ja')
def race_ja(value):
    """Translate race/type to Japanese."""
    return RACE_JA.get(str(value).lower(), value)


@register.filter(name='rarity_ja')
def rarity_ja(value):
    """Translate rarity to Japanese."""
    return RARITY_JA.get(str(value).lower(), value)


@register.filter(name='source_ja')
def source_ja(value):
    """Translate price source name to Japanese."""
    return SOURCE_JA.get(str(value), value)


@register.filter(name='usd_to_jpy')
def usd_to_jpy(value):
    """Convert USD decimal to integer JPY using configured exchange rate."""
    try:
        rate = getattr(settings, 'USD_TO_JPY_RATE', 150.0)
        return int(float(value) * rate)
    except (TypeError, ValueError):
        return None


@register.filter(name='eur_to_jpy')
def eur_to_jpy(value):
    """Convert EUR decimal to integer JPY using configured exchange rate."""
    try:
        rate = getattr(settings, 'EUR_TO_JPY_RATE', 160.0)
        return int(float(value) * rate)
    except (TypeError, ValueError):
        return None


@register.filter(name='jpy')
def jpy(value):
    """Format an integer as JPY: ¥1,234"""
    try:
        return f'¥{int(value):,}'
    except (TypeError, ValueError):
        return '—'

@register.filter(name='link_arrows')
def link_arrows(linkmarkers):
    """Convert ['Top', 'Bottom-Left', ...] to arrows like ↑ ↙"""
    if not linkmarkers: return ''
    mapping = {
        'Top': '↑', 'Bottom': '↓', 'Left': '←', 'Right': '→',
        'Top-Left': '↖', 'Top-Right': '↗', 'Bottom-Left': '↙', 'Bottom-Right': '↘'
    }
    arrows = [mapping.get(m.strip(), '') for m in str(linkmarkers).split(',')]
    return ''.join(arrows)

@register.filter(name='detailed_race')
def detailed_race(card):
    """
    Format: 種族／特殊タイプ／効果
    e.g. 悪魔族／エクシーズ／ペンデュラム／効果
    """
    if not card: return ''
    
    parts = []
    # 1. Race
    if card.race:
        parts.append(RACE_JA.get(str(card.race).lower(), card.race))
    
    if not card.card_type:
        return '／'.join(parts) if parts else ''
        
    ctype = str(card.card_type).lower()
    
    # If not a monster, just return its overall type
    if 'monster' not in ctype:
        res = CARD_TYPE_JA.get(ctype, card.card_type)
        if parts: return f"{parts[0]}／{res}"
        return res
        
    # 2. Sub-types (Fusion, Synchro, Xyz, Link, Ritual, Pendulum)
    if 'fusion' in ctype: parts.append('融合')
    if 'synchro' in ctype: parts.append('シンクロ')
    if 'xyz' in ctype: parts.append('エクシーズ')
    if 'link' in ctype: parts.append('リンク')
    if 'ritual' in ctype: parts.append('儀式')
    if 'pendulum' in ctype: parts.append('ペンデュラム')
    
    # Special types
    if 'toon' in ctype: parts.append('トゥーン')
    if 'spirit' in ctype: parts.append('スピリット')
    if 'union' in ctype: parts.append('ユニオン')
    if 'gemini' in ctype: parts.append('デュアル')
    if 'flip' in ctype: parts.append('リバース')
    if 'tuner' in ctype: parts.append('チューナー')
    
    # 3. Normal / Effect
    if 'effect' in ctype:
        parts.append('効果')
    elif 'normal' in ctype:
        parts.append('通常')
        
    return '／'.join(parts)
