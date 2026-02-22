import os
import django

# Set up Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "yugioh_price.settings.development")
django.setup()

from cards.models import Card, CardSet

def run():
    print("--- データベースのクリーニング開始 ---")
    
    # 1. TCG（海外版）のCardSetを削除
    # criteria: If price_available is True (which only TCG APIs had) or sets from API directly
    # Since we added OCG sets manually, they have price_available=False currently, and no TCGPlayer/Cardmarket prices.
    # Alternatively, any CardSet that does NOT end with -JP or -JA and does not come from our scraped OCG format.
    # Actually, simpler: delete all CardSets that have an API price, because we are removing all overseas pricing entirely.
    # Wait, the prompt says "海外の収録商品名はデータベースのカードも含めてすべて削除してください".
    
    # To be perfectly safe and comprehensive, let's delete any CardSet where price_available is True
    # or where set_code does not look like an OCG code and we want to wipe it.
    # We can just fetch all sets that have a price (since YGOPRODeck provided them) and delete them.
    tcg_sets = CardSet.objects.filter(price_available=True)
    count = tcg_sets.count()
    tcg_sets.delete()
    print(f"{count}件の海外CardSetを削除しました。")
    
    # Also delete any other sets that don't have a Japanese set name.
    # Our scraped sets from the wiki have set_name_ja populated.
    non_ja_sets = CardSet.objects.filter(set_name_ja='')
    count2 = non_ja_sets.count()
    non_ja_sets.delete()
    print(f"{count2}件の日本語名のないCardSetを削除しました。")

    # 2. 英語カード名/テキストの上書き
    cards = Card.objects.all()
    updated = 0
    for card in cards:
        changed = False
        if card.name_ja and card.name != card.name_ja:
            card.name = card.name_ja
            changed = True
        
        if card.description_ja and card.description != card.description_ja:
            card.description = card.description_ja
            changed = True
            
        if changed:
            card.save(update_fields=['name', 'description'])
            updated += 1
            
    print(f"{updated}件のカードの英語名・英語テキストを日本語で上書きしました。")
    print("--- 完了 ---")

if __name__ == '__main__':
    run()
