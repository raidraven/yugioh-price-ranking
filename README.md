# 遊戯王カード最安値ランキング

Djangoで作成した遊戯王カードの価格比較・最安値ランキングWebアプリです。

## 機能

- 🏆 **最安値TOP10ランキング** — 毎朝7時に自動更新
- 🔍 **カード検索** — 検索したカードは自動的にDBに保存
- 📄 **カード詳細ページ** — 価格比較表・カード効果・レアリティ情報
- 🌐 **無料API使用** — [YGOPRODeck API](https://ygoprodeck.com/api-guide/)

## データソース

[YGOPRODeck](https://ygoprodeck.com/) の公開APIを利用しています。
価格情報：TCGPlayer・Cardmarket・eBay・Amazon

## ローカル環境での実行

```bash
# 仮想環境の有効化
.\venv\Scripts\activate

# 開発サーバー起動
$env:DJANGO_SETTINGS_MODULE="yugioh_price.settings.development"
python manage.py runserver
```

ブラウザで http://localhost:8000 にアクセスしてください。

## 価格の手動更新

```bash
python manage.py update_prices
```

## デプロイ

Render.com にデプロイ済み。`render.yaml` を参照。
