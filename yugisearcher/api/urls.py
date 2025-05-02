from django.urls import path
from . import views

urlpatterns = [
    path("yugisearcher/", views.CardListCreate.as_view(), name="carddata-view-create"),
    path("inventory/", views.fetch_card_inventory, name='home'),
    path('search/', views.searcher, name='searcher'),
    path('clear_card_data/', views.clear_card_data, name='clear_card_data'),
    path('retrieve_card_data/', views.retrieve_card_data, name='retrieve_card_data'),
    path('get_progress/', views.get_progress, name='get_progress'),
    path('import_card_artwork/', views.import_card_artwork, name='import_card_artwork'),
    path("", views.searcher, name='searcher')
]