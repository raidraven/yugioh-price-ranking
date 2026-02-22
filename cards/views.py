import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.db import models
from django.db.models import Q
from .models import Card, CardSet
from . import services, api_client


logger = logging.getLogger(__name__)


def ranking_view(request):
    """
    Home page: Top 10 most-accessed cards (popularity ranking).
    """
    # Seed DB with popular cards on first visit
    if not Card.objects.exists():
        _seed_popular_cards()

    top10_cards = (
        Card.objects
        .filter(card_sets__isnull=False)
        .order_by('-view_count')
        .distinct()[:10]
    )

    # Build a list of (card, best_cardset) tuples for the template
    top10 = []
    for card in top10_cards:
        best_cs = (
            card.card_sets
            .filter(price_available=True, min_price__isnull=False, min_price__gt=0)
            .order_by('min_price')
            .first()
        )
        if best_cs is None:
            best_cs = card.card_sets.first()
        if best_cs:
            top10.append(best_cs)

    from django.utils import timezone
    last_updated = (
        CardSet.objects
        .filter(price_updated_at__isnull=False)
        .order_by('-price_updated_at')
        .values_list('price_updated_at', flat=True)
        .first()
    )

    return render(request, 'cards/ranking.html', {
        'top10': top10,
        'last_updated': last_updated,
    })


def search_view(request):
    """
    Search for cards. If a card is not in DB, fetch from API and store it.
    """
    query = request.GET.get('q', '').strip()
    results = []
    error = None
    not_found = False

    if query:
        # 1. Search local DB first
        db_results = Card.objects.filter(
            Q(name__icontains=query) | Q(name_ja__icontains=query)
        )[:20]

        if db_results.exists():
            results = list(db_results)
        else:
            # 2. Not in DB — fetch from API (fuzzy search, try English first)
            api_results = api_client.search_cards_by_name(query)

            # 3. If no hit, try Japanese API
            if not api_results:
                ja_results = api_client.search_cards_ja_by_name(query)
                if ja_results:
                    # Map to English reference data for standard syncing
                    for ja_data in ja_results[:10]:
                        en_data = api_client.fetch_card_by_id(ja_data['id'])
                        if en_data:
                            api_results.append(en_data)

            if api_results:
                for api_data in api_results[:10]:
                    card = services.sync_card_from_api_data(api_data)
                    if card:
                        # Fetch and sync Japanese data right away
                        ja_data = api_client.fetch_card_ja_by_id(card.card_id)
                        if ja_data:
                            services.sync_ja_data(card, ja_data)
                            card.refresh_from_db()
                        results.append(card)
            else:
                not_found = True

    return render(request, 'cards/search.html', {
        'query': query,
        'results': results,
        'not_found': not_found,
        'error': error,
    })


def card_detail_view(request, card_id: int):
    """
    Card detail page. If card is not in DB, fetch and store it first.
    """
    card = Card.objects.filter(card_id=card_id).first()

    if not card:
        api_data = api_client.fetch_card_by_id(card_id)
        if api_data:
            card = services.sync_card_from_api_data(api_data)
        if not card:
            return render(request, 'cards/not_found.html', {
                'card_id': card_id,
            }, status=404)

    card_sets = card.card_sets.all().order_by('min_price')
    has_price = card_sets.filter(price_available=True, min_price__isnull=False).exists()
    best_set = card_sets.filter(price_available=True, min_price__isnull=False).first()
    artworks = card.artworks.order_by('artwork_index')

    # Increment view count for popularity ranking
    Card.objects.filter(pk=card.pk).update(view_count=models.F('view_count') + 1)

    return render(request, 'cards/card_detail.html', {
        'card': card,
        'card_sets': card_sets,
        'has_price': has_price,
        'best_set': best_set,
        'artworks': artworks,
    })


def _seed_popular_cards():
    """Seed DB with popular Yu-Gi-Oh cards on first visit."""
    popular_names = [
        'Dark Magician',
        'Blue-Eyes White Dragon',
        'Exodia the Forbidden One',
        'Blue-Eyes Ultimate Dragon',
        'Swords of Revealing Light',
        'Mirror Force',
        'Pot of Greed',
        'Monster Reborn',
        'Red-Eyes Black Dragon',
        'Harpie Lady',
    ]
    for name in popular_names:
        try:
            services.get_or_fetch_card(name)
        except Exception as e:
            logger.error('Failed to seed card %s: %s', name, e)


def deck_calculator_view(request):
    """
    Deck Price Calculator.
    Accepts text list, YDKE URL, or image upload (OCR).
    """
    from .deck_calc import (
        parse_text_deck, decode_ydke, ocr_image,
        lookup_cards_from_names, lookup_cards_from_ids,
    )

    context: dict = {'input_type': 'text'}

    if request.method != 'POST':
        return render(request, 'cards/deck_calculator.html', context)

    input_type = request.POST.get('input_type', 'text')
    context['input_type'] = input_type

    results = []
    not_found = []
    ocr_raw = None
    error = None

    try:
        if input_type == 'image':
            image = request.FILES.get('deck_image')
            if not image:
                error = '画像ファイルが選択されていません。'
            else:
                raw, ocr_err = ocr_image(image)
                if ocr_err:
                    error = ocr_err
                else:
                    ocr_raw = raw
                    card_list = parse_text_deck(raw)
                    if not card_list:
                        error = 'カード名を読み取れませんでした。別の画像か、テキスト入力をお試しください。'
                    else:
                        results, not_found = lookup_cards_from_names(card_list)

        elif input_type == 'ydke':
            url = request.POST.get('ydke_url', '').strip()
            context['ydke_url'] = url
            if not url:
                error = 'YDKE リンクを入力してください。'
            elif not url.lower().startswith('ydke://'):
                error = '無効な YDKE リンクです。ydke:// で始まる URL を入力してください。'
            else:
                id_counter = decode_ydke(url)
                if not id_counter:
                    error = 'YDKE の解析に失敗しました。正しい形式かご確認ください。'
                else:
                    results, not_found = lookup_cards_from_ids(id_counter)

        else:  # text
            text = request.POST.get('deck_text', '').strip()
            context['deck_text'] = text
            if not text:
                error = 'デッキリストを入力してください。'
            else:
                card_list = parse_text_deck(text)
                if not card_list:
                    error = 'カード名を解析できませんでした。フォーマットをご確認ください。'
                else:
                    results, not_found = lookup_cards_from_names(card_list)

    except Exception as e:
        logger.exception('deck_calculator_view error')
        error = f'処理中にエラーが発生しました: {e}'

    total_jpy = sum(r['subtotal_jpy'] for r in results)

    context.update({
        'results': results,
        'not_found': not_found,
        'total_jpy': total_jpy,
        'ocr_raw': ocr_raw,
        'error': error,
        'show_results': bool(results or not_found or error),
    })
    return render(request, 'cards/deck_calculator.html', context)


def inquiry_view(request):
    from django.contrib import messages
    from .models import Inquiry
    
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message_text = request.POST.get('message', '').strip()
        
        if name and email and message_text:
            Inquiry.objects.create(name=name, email=email, message=message_text)
            messages.success(request, 'お問い合わせを送信しました。')
            return redirect('cards:inquiry')
        else:
            messages.error(request, 'すべての項目を正しく入力してください。')
            
    return render(request, 'cards/inquiry.html')
