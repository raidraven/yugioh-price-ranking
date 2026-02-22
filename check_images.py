import requests
resp = requests.get('https://db.ygoprodeck.com/api/v7/cardinfo.php', params={'name': 'Dark Magician', 'misc': 'yes'}, timeout=15)
data = resp.json()['data'][0]
images = data.get('card_images', [])
print(f"Total artworks: {len(images)}")
for i, img in enumerate(images):
    print(f"  [{i}] id={img['id']} url={img['image_url']}")
# Also check card_sets to see which are OCG
sets = data.get('card_sets', [])
print(f"\nTotal sets: {len(sets)}")
for s in sets[:10]:
    print(f"  {s.get('set_code')} | {s.get('set_name')} | {s.get('set_rarity')}")
