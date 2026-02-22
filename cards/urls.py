from django.urls import path
from . import views

app_name = 'cards'

urlpatterns = [
    path('', views.ranking_view, name='ranking'),
    path('search/', views.search_view, name='search'),
    path('card/<int:card_id>/', views.card_detail_view, name='card_detail'),
    path('deck-calculator/', views.deck_calculator_view, name='deck_calculator'),
    path('inquiry/', views.inquiry_view, name='inquiry'),
]
