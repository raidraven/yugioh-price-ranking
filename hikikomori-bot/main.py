"""
main.py - 引きこもりBotのエントリーポイント

使い方:
  python main.py            # スケジューラ起動（通常モード）
  python main.py --dry-run  # スケジューラ起動（DRY RUNモード・実際に投稿しない）
  python main.py --once     # 1回だけ投稿してすぐ終了
  python main.py --once --dry-run  # 1回だけ生成してターミナルに表示（APIキー不要）
"""

import argparse
import sys
from generator import generate_tweet
from poster import post_tweet
from scheduler import start_scheduler


def main():
    parser = argparse.ArgumentParser(
        description="引きこもりテーマ X Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際には投稿せず、生成したツイートをターミナルに表示する",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="1回だけ投稿してすぐ終了する（テスト用）",
    )
    args = parser.parse_args()

    if args.once:
        # 1回投稿モード
        print("🤖 1回投稿モード" + (" (DRY RUN)" if args.dry_run else ""))
        try:
            category_name, tweet_text = generate_tweet()
            print(f"\n📂 カテゴリ: [{category_name}]")
            post_tweet(tweet_text, dry_run=args.dry_run)
        except Exception as e:
            print(f"❌ エラー: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # スケジューラモード
        try:
            start_scheduler(dry_run=args.dry_run)
        except KeyboardInterrupt:
            print("\n\n👋 Botを停止しました。")


if __name__ == "__main__":
    main()
