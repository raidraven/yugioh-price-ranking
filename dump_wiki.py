# -*- coding: utf-8 -*-
import urllib.request
import urllib.parse
query = urllib.parse.quote('ブラック・マジシャン'.encode('euc-jp', errors='ignore'))
url = f'https://yugioh-wiki.net/index.php?{query}'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as response:
    html = response.read().decode('euc-jp', errors='ignore')
    with open('wiki_dump.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Dumped to wiki_dump.html")
