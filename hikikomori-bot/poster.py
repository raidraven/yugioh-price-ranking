"""
poster.py - tweepyを使ってX(Twitter)へ投稿するモジュール
"""

import os
import tweepy
from dotenv import load_dotenv

load_dotenv()


def get_client() -> tweepy.Client:
    """tweepy v2 クライアントを初期化して返す"""
    return tweepy.Client(
        bearer_token=os.getenv("X_BEARER_TOKEN"),
        consumer_key=os.getenv("X_API_KEY"),
        consumer_secret=os.getenv("X_API_SECRET"),
        access_token=os.getenv("X_ACCESS_TOKEN"),
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
        wait_on_rate_limit=True,
    )


def post_tweet(text: str, dry_run: bool = False) -> bool:
    """
    ツイートを投稿する。
    Args:
        text: ツイート本文
        dry_run: Trueの場合は実際には投稿せずターミナルに出力するだけ
    Returns:
        成功した場合 True
    """
    if dry_run:
        print(f"\n{'='*50}")
        print("【DRY RUN - 実際には投稿されません】")
        print(f"{'='*50}")
        print(text)
        print(f"{'='*50}")
        print(f"文字数: {len(text)}/140\n")
        return True

    try:
        client = get_client()
        response = client.create_tweet(text=text)
        tweet_id = response.data["id"]
        print(f"✅ 投稿成功！ Tweet ID: {tweet_id}")
        print(f"   URL: https://x.com/i/web/status/{tweet_id}")
        return True
    except tweepy.TweepyException as e:
        print(f"❌ 投稿失敗: {e}")
        return False
    except Exception as e:
        print(f"❌ 予期しないエラー: {e}")
        return False
