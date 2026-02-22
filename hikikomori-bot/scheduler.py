"""
scheduler.py - 定期投稿スケジューラ
1日4回（朝・昼・夕方・深夜）自動投稿する
"""

import schedule
import time
import logging
from datetime import datetime
from generator import generate_tweet
from poster import post_tweet

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# 投稿スケジュール（時刻は変更可能）
POST_TIMES = [
    "08:30",  # 朝（引きこもりが起き始める時間帯）
    "13:00",  # 昼
    "18:00",  # 夕方
    "23:30",  # 深夜（引きこもりが活発になる時間帯）
]


def job(dry_run: bool = False):
    """1回分の投稿ジョブ"""
    logger.info("投稿ジョブ開始...")
    try:
        category_name, tweet_text = generate_tweet()
        logger.info(f"カテゴリ: [{category_name}]")
        logger.info(f"生成テキスト ({len(tweet_text)}文字): {tweet_text}")

        success = post_tweet(tweet_text, dry_run=dry_run)
        if success:
            logger.info("ジョブ完了 ✅")
        else:
            logger.error("投稿失敗 ❌")

    except Exception as e:
        logger.error(f"ジョブでエラーが発生しました: {e}")


def start_scheduler(dry_run: bool = False):
    """スケジューラを起動してループする"""
    for post_time in POST_TIMES:
        schedule.every().day.at(post_time).do(job, dry_run=dry_run)
        logger.info(f"スケジュール登録: 毎日 {post_time} に投稿")

    logger.info("\n🤖 引きこもりBot スケジューラ起動中...")
    logger.info(f"投稿時刻: {', '.join(POST_TIMES)}")
    if dry_run:
        logger.info("⚠️  DRY RUNモード: 実際には投稿されません\n")

    while True:
        schedule.run_pending()
        next_run = schedule.next_run()
        if next_run:
            remaining = next_run - datetime.now()
            total_seconds = int(remaining.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            print(
                f"\r⏳ 次の投稿まで: {hours:02d}:{minutes:02d}:{seconds:02d} "
                f"({next_run.strftime('%H:%M')})",
                end="",
                flush=True,
            )
        time.sleep(1)
