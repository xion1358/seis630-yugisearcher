from django.urls import path
from . import views

urlpatterns = [
    path("yugisearcher/", views.CardListCreate.as_view(), name="carddata-view-create"),
    path("inventory/", views.fetch_card_inventory, name='home'),
    path('search/', views.searcher, name='searcher'),
    path('clear_card_data/', views.clear_card_data, name='clear_card_data'),
    path("", views.searcher, name='searcher')
]