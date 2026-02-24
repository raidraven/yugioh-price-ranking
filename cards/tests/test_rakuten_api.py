import unittest
from unittest.mock import patch, MagicMock
from django.test import override_settings

from cards.rakuten_api import fetch_min_price

class RakutenAPITest(unittest.TestCase):
    
    @override_settings(RAKUTEN_APPLICATION_ID='test_app_id')
    @patch('cards.rakuten_api.time.sleep')
    @patch('cards.rakuten_api.requests.get')
    def test_fetch_min_price_success(self, mock_get, mock_sleep):
        """テスト: APIから正常に価格が取得できるケース"""
        # モックのレスポンスを設定
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Items": [
                {
                    "Item": {
                        "itemName": "青眼の白龍 遊戯王",
                        "itemPrice": 1500
                    }
                }
            ]
        }
        mock_get.return_value = mock_response

        # テスト実行
        price = fetch_min_price("青眼の白龍")

        # アサーション
        self.assertEqual(price, 1500)
        mock_get.assert_called_once()
        # パラメータの確認
        args, kwargs = mock_get.call_args
        self.assertEqual(kwargs['params']['keyword'], "青眼の白龍 遊戯王")
        self.assertEqual(kwargs['params']['sort'], "+itemPrice")

    @override_settings(RAKUTEN_APPLICATION_ID='test_app_id')
    @patch('cards.rakuten_api.time.sleep')
    @patch('cards.rakuten_api.requests.get')
    def test_fetch_min_price_not_found(self, mock_get, mock_sleep):
        """テスト: 検索結果が0件のケース"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Items": []}  # 空のリスト
        mock_get.return_value = mock_response

        price = fetch_min_price("存在しないカード名")

        self.assertIsNone(price)

    @override_settings(RAKUTEN_APPLICATION_ID='test_app_id')
    @patch('cards.rakuten_api.time.sleep')
    @patch('cards.rakuten_api.requests.get')
    def test_fetch_min_price_api_error(self, mock_get, mock_sleep):
        """テスト: APIがエラー(429など)を返したケース"""
        mock_response = MagicMock()
        mock_response.status_code = 429 # Rate Limit Exceeded
        mock_get.return_value = mock_response

        price = fetch_min_price("レッドアイズ")

        self.assertIsNone(price)

    @override_settings(RAKUTEN_APPLICATION_ID=None)
    def test_fetch_min_price_no_app_id(self):
        """テスト: RAKUTEN_APPLICATION_ID が設定されていないケース"""
        # APIリクエスト自体が行われないはず
        price = fetch_min_price("ブラック・マジシャン")
        self.assertIsNone(price)

    @override_settings(RAKUTEN_APPLICATION_ID='test_app_id')
    def test_fetch_min_price_empty_name(self):
        """テスト: カード名が空のケース"""
        price = fetch_min_price("")
        self.assertIsNone(price)
