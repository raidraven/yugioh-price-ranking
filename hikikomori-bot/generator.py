"""
generator.py - OpenAI APIを使ってツイート文を生成するモジュール
"""

import os
from openai import OpenAI
from dotenv import load_dotenv
from prompts import SYSTEM_PROMPT, get_random_prompt

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

MAX_TWEET_LENGTH = 140
MAX_RETRIES = 3


def generate_tweet() -> tuple[str, str]:
    """
    OpenAI GPT-4o-miniを使ってツイートを生成する。
    Returns:
        (カテゴリ名, ツイート本文) のタプル
    Raises:
        ValueError: 有効なツイートを生成できなかった場合
    """
    category_name, instruction = get_random_prompt()

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": instruction},
                ],
                max_tokens=200,
                temperature=0.9,  # 少し高めにして多様性を出す
            )

            tweet = response.choices[0].message.content.strip()

            # 文字数バリデーション（X上では1文字=1カウント）
            if len(tweet) <= MAX_TWEET_LENGTH:
                return category_name, tweet
            else:
                # 140字超えたら末尾をカットして省略
                print(f"  [警告] 生成されたツイートが{len(tweet)}文字のため短縮します (試行 {attempt}/{MAX_RETRIES})")
                if attempt == MAX_RETRIES:
                    # 最終試行では強制的にカット
                    return category_name, tweet[:MAX_TWEET_LENGTH]

        except Exception as e:
            print(f"  [エラー] OpenAI API呼び出し失敗 (試行 {attempt}/{MAX_RETRIES}): {e}")
            if attempt == MAX_RETRIES:
                raise ValueError(f"ツイートの生成に{MAX_RETRIES}回失敗しました: {e}") from e

    raise ValueError("ツイートの生成に失敗しました")
