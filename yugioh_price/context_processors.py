from django.conf import settings

def google_analytics(request):
    """
    Google Analyticsの測定IDを全テンプレートのコンテキストに追加する
    """
    return {
        'GOOGLE_ANALYTICS_ID': getattr(settings, 'GOOGLE_ANALYTICS_ID', None)
    }
