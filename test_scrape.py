# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
import re

def get_wiki_sets(card_name):
    print(f"Fetching {card_name}...")
    brackets = '《'.encode('euc-jp') + card_name.encode('euc-jp', errors='ignore') + '》'.encode('euc-jp')
    query = urllib.parse.quote(brackets)
    url = f'https://yugioh-wiki.net/index.php?{query}'
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('euc-jp', errors='ignore')
            
            idx = html.find('id="pack"')
            if idx == -1: return ['No pack id found']
            
            # Find the first <ul> after the h3 tag
            ul_idx = html.find('<ul', idx)
            if ul_idx == -1: return ['No ul found']
            
            ul_end = html.find('</ul>', ul_idx)
            if ul_end == -1: return ['No ul end found']
            
            ul_chunk = html[ul_idx:ul_end]
            items = re.findall(r'<li>(.*?)</li>', ul_chunk, re.DOTALL)
            
            clean_items = []
            for i in items:
                # Remove nested tags like <a href=...>...</a> and <span>...</span>
                clean = re.sub(r'<[^>]+>', '', i)
                # Wiki appends rarity like "Ultra", we can keep or strip it
                clean_items.append(clean.strip())
            return clean_items
    except Exception as e:
        return [f"Error: {e}"]

if __name__ == '__main__':
    for card in ['ブラック・マジシャン', 'ブラック・ローズ・ドラゴン', '黒魔女ディアベルスター']:
        sets = get_wiki_sets(card)
        print(f"--- {card} ---")
        for s in sets[:5]: print(s)
