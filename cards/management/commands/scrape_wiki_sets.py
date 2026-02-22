from django.core.management.base import BaseCommand
from cards.models import Card
from cards.wiki_scraper import apply_wiki_sets_to_card
import time

class Command(BaseCommand):
    help = 'Scrape Yugioh Wiki for Japanese Set Names for all cards'

    def handle(self, *args, **options):
        cards = Card.objects.exclude(name_ja='').exclude(name_ja=None)
        total = cards.count()
        self.stdout.write(f"Found {total} cards with Japanese names to process.")
        
        updated_count = 0
        for i, card in enumerate(cards):
            self.stdout.write(f"[{i+1}/{total}] Processing {card.name_ja}...")
            try:
                if apply_wiki_sets_to_card(card):
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f"  -> Updated sets for {card.name_ja}"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  -> Error on {card.name_ja}: {e}"))
            
            # Be nice to the wiki server
            time.sleep(1)
            
        self.stdout.write(self.style.SUCCESS(f"Finished! Updated sets for {updated_count} cards."))
