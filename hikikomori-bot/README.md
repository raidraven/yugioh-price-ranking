# 🏠 引きこもりBot - X自動投稿Bot

引きこもりをテーマにした共感・癒し系ツイートをAIが自動生成し、定期的にX(Twitter)へ投稿するBotです。

---

## 📦 必要なもの

- Python 3.10 以上
- X Developer Account（API v2 アクセス権）
- OpenAI API キー

---

## 🚀 セットアップ手順

### 1. ライブラリのインストール

```powershell
cd C:\Users\loner\.gemini\antigravity\scratch\hikikomori-bot
pip install -r requirements.txt
```

### 2. APIキーの設定

`.env.example` をコピーして `.env` ファイルを作成し、各APIキーを記入します。

```powershell
copy .env.example .env
```

`.env` をメモ帳などで開いて編集：
```
X_API_KEY=取得したキーを貼り付け
X_API_SECRET=取得したシークレットを貼り付け
X_ACCESS_TOKEN=取得したトークンを貼り付け
X_ACCESS_TOKEN_SECRET=取得したシークレットを貼り付け
X_BEARER_TOKEN=取得したBearer Tokenを貼り付け
OPENAI_API_KEY=取得したOpenAI APIキーを貼り付け
```

### 3. X APIキーの取得方法

1. [developer.twitter.com](https://developer.twitter.com) にアクセス
2. 「Create Project」→「Create App」を作成
3. 「Keys and Tokens」からAPIキーを取得
4. **重要**: App SettingsでApp permissionsを「Read and Write」に変更

---

## ▶️ 使い方

### ① ツイートをターミナルで確認する（APIキー不要・まずはここから）

```powershell
python main.py --once --dry-run
```

→ AIが生成したツイートがターミナルに表示されます。

### ② 1回だけ実際に投稿してテスト

```powershell
python main.py --once
```

### ③ スケジューラを起動（本番運用）

```powershell
python main.py
```

→ 毎日 **08:30 / 13:00 / 18:00 / 23:30** に自動投稿します。
→ 止めるには `Ctrl + C`

### ④ DRY RUNモードでスケジューラを起動（実際には投稿しない）

```powershell
python main.py --dry-run
```

---

## ⏰ 投稿時刻の変更

`scheduler.py` の `POST_TIMES` リストを編集してください：

```python
POST_TIMES = [
    "08:30",  # 朝
    "13:00",  # 昼
    "18:00",  # 夕方
    "23:30",  # 深夜
]
```

---

## 💰 収益化のヒント

1. **Xサブスクリプション（スーパーフォロー）**
   - 限定コンテンツを提供してフォロワーに課金

2. **アフィリエイト**
   - 引きこもり・メンタルヘルス系の書籍や商品リンクをツイートに自然に組み込む

3. **noteや有料コンテンツへの誘導**
   - 引きこもり体験記や克服記事への誘導

---

## 📁 ファイル構成

```
hikikomori-bot/
├── main.py         # エントリーポイント
├── generator.py    # OpenAIでツイート生成
├── poster.py       # Xへの投稿
├── scheduler.py    # 定期投稿スケジューラ
├── prompts.py      # プロンプトテンプレート集
├── .env            # APIキー（Gitにコミットしないこと！）
├── .env.example    # APIキーのテンプレート
└── requirements.txt
```
