"""
Management command: manually trigger the price update job.
Usage: python manage.py update_prices
"""
from django.core.management.base import BaseCommand
from cards.services import update_all_prices


class Command(BaseCommand):
    help = '全カードの価格をYGOPRODeck APIから更新します'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max', type=int, default=500,
            help='更新するカードの最大数 (デフォルト: 500)'
        )

    def handle(self, *args, **options):
        max_cards = options['max']
        self.stdout.write(f'価格更新開始 (最大 {max_cards} 枚)...')
        count = update_all_prices(max_cards=max_cards)
        self.stdout.write(self.style.SUCCESS(f'完了: {count} 枚のカードを更新しました。'))
