import logging
import requests
import time
from urllib.parse import quote
from django.conf import settings

logger = logging.getLogger(__name__)

RAKUTEN_API_BASE = 'https://app.rakuten.co.jp/services/api/IchibaItem/Search/20220601'
DELAY = 1.0  # 楽天APIの制限 (1req/sec) に合わせたディレイ

class RakutenAPIError(Exception):
    pass


def fetch_min_price(card_name_ja: str) -> tuple[int | None, str | None]:
    """
    楽天ブックス/市場APIを使用して、指定されたカード名（日本語）の最安値を取得します。
    「{card_name_ja} 遊戯王」で検索し、価格の安い順にソートします。
    戻り値は (価格(int), アフィリエイトURL(str)) のタプルです。
    """
    app_id = getattr(settings, 'RAKUTEN_APPLICATION_ID', None)
    affiliate_id = getattr(settings, 'RAKUTEN_AFFILIATE_ID', None)
    if not app_id:
        logger.warning('RAKUTEN_APPLICATION_ID is not configured.')
        return None, None

    if not card_name_ja:
        return None, None

    # 特殊文字があると検索に失敗しやすいため、整形する（例: 「ブラック・マジシャン」 -> 「ブラックマジシャン」などは要調整だが、一旦そのまま空白区切りにする）
    # 遊戯王のカードであることを明示
    query = f"{card_name_ja} 遊戯王"

    params = {
        'applicationId': app_id,
        'keyword': query,
        'sort': '+itemPrice',  # 価格の安い順
        'hits': 1,            # 最安値1件だけ取得できればよい
        'imageFlag': 1,       # 画像がある商品（ノイズを減らすため）
    }
    if affiliate_id:
        params['affiliateId'] = affiliate_id

    try:
        # 連続リクエストによる制限を避けるためのスリープ
        time.sleep(DELAY)
        
        resp = requests.get(RAKUTEN_API_BASE, params=params, timeout=10)
        
        if resp.status_code == 200:
            data = resp.json()
            if data.get('Items'):
                # 最初のアイテム（最安値）の価格を返す
                item = data['Items'][0]['Item']
                price = item.get('itemPrice')
                item_url = item.get('affiliateUrl') or item.get('itemUrl')
                if price:
                    return int(price), item_url
            else:
                logger.info(f'Rakuten API: No items found for "{query}"')
                return None, None
        elif resp.status_code == 429:
            logger.warning('Rakuten API Rate Limit Exceeded (429).')
            return None, None
        else:
            logger.error(f'Rakuten API error {resp.status_code}: {resp.text}')
            return None, None
            
    except requests.RequestException as e:
        logger.error(f'Rakuten API request failed: {e}')
        return None, None

