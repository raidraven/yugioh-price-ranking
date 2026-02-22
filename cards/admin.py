from django.contrib import admin
from .models import Card, CardSet, Inquiry


@admin.register(Card)
class CardAdmin(admin.ModelAdmin):
    list_display = ['name', 'card_id', 'card_type', 'attribute', 'level', 'created_at']
    search_fields = ['name', 'name_ja', 'card_id']
    list_filter = ['card_type', 'attribute', 'frame_type']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CardSet)
class CardSetAdmin(admin.ModelAdmin):
    list_display = ['card', 'set_code', 'set_rarity', 'min_price', 'min_price_source',
                    'price_available', 'price_updated_at']
    search_fields = ['card__name', 'set_code', 'set_name']
    list_filter = ['price_available', 'set_rarity']
    readonly_fields = ['price_updated_at']

@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'created_at']
    search_fields = ['name', 'email', 'message']
    readonly_fields = ['name', 'email', 'message', 'created_at']

    def has_add_permission(self, request):
        return False
