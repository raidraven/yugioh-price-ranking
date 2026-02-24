import time
from django.core.management.base import BaseCommand
from cards.models import Card
from cards.wiki_scraper import apply_wiki_sets_to_card

class Command(BaseCommand):
    help = 'Update Japanese descriptions and sets for all cards using Yugioh Wiki'

    def handle(self, *args, **options):
        cards = Card.objects.all()
        updated_count = 0
        self.stdout.write(f"Updating {cards.count()} cards from Wiki...")
        
        for card in cards:
            if card.name_ja:
                self.stdout.write(f"Scraping wiki for: {card.name_ja}...")
                updated = apply_wiki_sets_to_card(card)
                if updated:
                    updated_count += 1
                    self.stdout.write(self.style.SUCCESS(f" -> Updated {card.name_ja}"))
                time.sleep(1.0) # wait to avoid overloading the wiki Server
        
        self.stdout.write(self.style.SUCCESS(f"Successfully updated {updated_count} cards."))
