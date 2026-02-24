from django.db import models
from django.utils import timezone



class Card(models.Model):
    """Represents a Yu-Gi-Oh! card cached from the YGOPRODeck API."""

    # Core identification
    card_id = models.IntegerField(unique=True, verbose_name='カードID (Passcode)')
    konami_id = models.IntegerField(null=True, blank=True, verbose_name='コナミID')
    name = models.CharField(max_length=300, verbose_name='カード名')
    name_ja = models.CharField(max_length=300, blank=True, verbose_name='カード名（日本語）')

    # Card details
    card_type = models.CharField(max_length=100, verbose_name='カードタイプ')
    frame_type = models.CharField(max_length=50, blank=True, verbose_name='フレームタイプ')
    description = models.TextField(verbose_name='カード効果・説明')
    description_ja = models.TextField(blank=True, verbose_name='カード効果・説明（日本語）')

    # Monster-specific
    atk = models.IntegerField(null=True, blank=True, verbose_name='ATK')
    def_points = models.IntegerField(null=True, blank=True, verbose_name='DEF')
    level = models.IntegerField(null=True, blank=True, verbose_name='レベル/ランク')
    scale = models.IntegerField(null=True, blank=True, verbose_name='ペンデュラムスケール')
    linkval = models.IntegerField(null=True, blank=True, verbose_name='リンク値')
    linkmarkers = models.CharField(max_length=200, blank=True, verbose_name='リンクマーカー')
    race = models.CharField(max_length=100, blank=True, verbose_name='種族')
    attribute = models.CharField(max_length=50, blank=True, verbose_name='属性')
    archetype = models.CharField(max_length=200, blank=True, verbose_name='アーキタイプ')

    # Page view count for popularity ranking
    view_count = models.IntegerField(default=0, verbose_name='アクセス数')

    # Rakuten Ichiba min price (JPY)
    rakuten_min_price = models.IntegerField(null=True, blank=True, verbose_name='楽天最安値 (¥)')
    rakuten_affiliate_url = models.URLField(max_length=1000, blank=True, null=True, verbose_name='楽天アフィリエイトURL')

    # Images (URLs from YGOPRODeck CDN — referenced, not downloaded)
    # Primary artwork (artwork index 0)
    image_url = models.URLField(max_length=500, blank=True, verbose_name='カード画像URL')
    image_url_small = models.URLField(max_length=500, blank=True, verbose_name='カード画像URL（小）')
    image_url_cropped = models.URLField(max_length=500, blank=True, verbose_name='カード画像URL（トリミング）')

    # Meta
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='作成日時')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新日時')
    api_url = models.URLField(max_length=500, blank=True, verbose_name='YGOPRODeck URL')

    class Meta:
        verbose_name = 'カード'
        verbose_name_plural = 'カード一覧'
        ordering = ['name']

    def __str__(self):
        return f'{self.name} (ID: {self.card_id})'

    def get_display_name(self):
        return self.name_ja if self.name_ja else self.name

    @property
    def all_artworks(self):
        """Return all stored artwork objects ordered by index."""
        return self.artworks.all().order_by('artwork_index')

    @property
    def ocg_artwork(self):
        """Return the OCG artwork (last index) if multiple artworks exist."""
        artworks = list(self.artworks.order_by('artwork_index'))
        if len(artworks) > 1:
            return artworks[-1]  # last artwork is typically OCG exclusive or alternate
        return artworks[0] if artworks else None

    @property
    def primary_artwork(self):
        """Return the first (primary/TCG) artwork."""
        return self.artworks.order_by('artwork_index').first()

    @property
    def official_url(self):
        """公式データベースへの検索リンク"""
        if self.konami_id:
            return f"https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=2&cid={self.konami_id}"
        import urllib.parse
        name = self.name_ja if self.name_ja else self.name
        query = urllib.parse.quote(name)
        return f"https://www.db.yugioh-card.com/yugiohdb/card_search.action?ope=1&sess=1&keyword={query}&stype=1"

    @property
    def wiki_url(self):
        """遊戯王Wikiへのページリンク（EUC-JPエンコード）"""
        import urllib.parse
        from .utils import to_full_width_for_wiki
        name = self.name_ja if self.name_ja else self.name
        name_fw = to_full_width_for_wiki(name)
        try:
            encoded_name = name_fw.encode('euc-jp', errors='ignore')
            brackets = '《'.encode('euc-jp') + encoded_name + '》'.encode('euc-jp')
            query = urllib.parse.quote(brackets)
            return f"https://yugioh-wiki.net/index.php?{query}"
        except Exception:
            query = urllib.parse.quote(f"site:yugioh-wiki.net {name}")
            return f"https://www.google.com/search?q={query}"


class CardSet(models.Model):
    """Represents a specific printing of a card (set + rarity)."""

    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='card_sets',
                              verbose_name='カード')
    set_name = models.CharField(max_length=300, verbose_name='セット名')
    set_name_ja = models.CharField(max_length=300, blank=True, verbose_name='セット名（日本語）')
    set_code = models.CharField(max_length=50, verbose_name='セットコード')
    set_rarity = models.CharField(max_length=100, verbose_name='レアリティ')
    set_rarity_code = models.CharField(max_length=20, blank=True, verbose_name='レアリティコード')

    # Prices cached from API (in USD via TCGPlayer/Cardmarket/etc.)
    cardmarket_price = models.DecimalField(max_digits=10, decimal_places=2,
                                           null=True, blank=True, verbose_name='Cardmarket価格 (€)')
    tcgplayer_price = models.DecimalField(max_digits=10, decimal_places=2,
                                           null=True, blank=True, verbose_name='TCGPlayer価格 ($)')
    ebay_price = models.DecimalField(max_digits=10, decimal_places=2,
                                      null=True, blank=True, verbose_name='eBay価格 ($)')
    amazon_price = models.DecimalField(max_digits=10, decimal_places=2,
                                        null=True, blank=True, verbose_name='Amazon価格 ($)')
    coolstuffinc_price = models.DecimalField(max_digits=10, decimal_places=2,
                                              null=True, blank=True, verbose_name='CoolStuffInc価格 ($)')

    # Computed minimum price across all sources (in the lowest-priced currency equivalent)
    min_price = models.DecimalField(max_digits=10, decimal_places=2,
                                     null=True, blank=True, verbose_name='最安値 ($)')
    min_price_source = models.CharField(max_length=50, blank=True, verbose_name='最安値ソース')
    price_updated_at = models.DateTimeField(null=True, blank=True, verbose_name='価格更新日時')
    price_available = models.BooleanField(default=True, verbose_name='価格取得可能')

    class Meta:
        verbose_name = 'カードセット'
        verbose_name_plural = 'カードセット一覧'
        unique_together = [('card', 'set_code')]
        ordering = ['min_price']

    def __str__(self):
        return f'{self.card.name} [{self.set_code}] {self.set_rarity}'

    def compute_min_price(self):
        """Compute and store the minimum price across all sources."""
        prices = {
            'TCGPlayer': self.tcgplayer_price,
            'Cardmarket': self.cardmarket_price,
            'eBay': self.ebay_price,
            'Amazon': self.amazon_price,
            'CoolStuffInc': self.coolstuffinc_price,
        }
        valid = {k: v for k, v in prices.items() if v and v > 0}
        if valid:
            source = min(valid, key=valid.get)
            self.min_price = valid[source]
            self.min_price_source = source
            self.price_available = True
        else:
            self.min_price = None
            self.min_price_source = ''
            self.price_available = False
        self.price_updated_at = timezone.now()


class CardArtwork(models.Model):
    """Stores each artwork image version for a card (from card_images[] in API)."""

    card = models.ForeignKey(Card, on_delete=models.CASCADE, related_name='artworks',
                             verbose_name='カード')
    artwork_index = models.IntegerField(verbose_name='アートワーク番号')  # 0-based from API
    image_id = models.IntegerField(verbose_name='画像ID')  # YGOPRODeck image ID
    image_url = models.URLField(max_length=500, verbose_name='画像URL（全体）')
    image_url_small = models.URLField(max_length=500, blank=True, verbose_name='画像URL（小）')
    image_url_cropped = models.URLField(max_length=500, blank=True, verbose_name='画像URL（クロップ）')

    class Meta:
        verbose_name = 'カードアートワーク'
        verbose_name_plural = 'カードアートワーク一覧'
        unique_together = [('card', 'artwork_index')]
        ordering = ['artwork_index']

    def __str__(self):
        label = 'OCG' if self.is_ocg else 'TCG'
        return f'{self.card.name} アートワーク#{self.artwork_index} ({label})'

    @property
    def is_ocg(self):
        """Artworks after index 0 that have a different image_id are alternates (often OCG)."""
        return self.artwork_index > 0

    @property
    def label(self):
        if self.artwork_index == 0:
            return 'TCG / 通常'
        return f'アートワーク {self.artwork_index + 1}'

class Inquiry(models.Model):
    name = models.CharField(max_length=100, verbose_name='お名前')
    email = models.EmailField(verbose_name='メールアドレス')
    message = models.TextField(verbose_name='お問い合わせ内容')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='送信日時')

    class Meta:
        verbose_name = 'お問い合わせ'
        verbose_name_plural = 'お問い合わせ一覧'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name}様からのお問い合わせ"
