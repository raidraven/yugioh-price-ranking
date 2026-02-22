import urllib.request
import json

url = 'https://db.ygoprodeck.com/api/v7/cardinfo.php?name=Dark+Magician&language=ja'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as res:
    data = json.loads(res.read())
    
sets = data['data'][0].get('card_sets', [])
print('First API sets:')
for s in sets[:15]:
    print(s.get('set_code'), '->', s.get('set_name'))

