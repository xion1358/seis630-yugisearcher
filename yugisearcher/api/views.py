import requests
from django.shortcuts import render
from django.core.paginator import Paginator
from rest_framework import generics
from django.db.models import Q

from .services.card_service import *
from .models import CardData, CardInventory
from .serializers import CardDataSerializer
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.shortcuts import redirect
from yugisearcher import constants
from django.http import HttpRequest, HttpResponse


# Create your views here.
class CardListCreate(generics.ListCreateAPIView):
    queryset = CardData.objects.using('default').all()
    serializer_class = CardDataSerializer

def fetch_card_inventory(request: HttpRequest):
    ygo_api_url = "https://db.ygoresources.com/data/idx/card/name/en"

    response = requests.get(ygo_api_url)

    if response.status_code == 200:
        return JsonResponse(response.json(), safe=False)
    else:
        return JsonResponse({"error": "Failed to get ygo card inventory"}, status=500)

def searcher(request) -> HttpResponse:
    query = request.GET.get('query', '')
    page_number = request.GET.get('page', 1)
    page_obj = None
    page_size = 10

    card_type = request.GET.get(constants.CARD_TYPE)
    level = request.GET.get(constants.CARD_LEVEL)
    rank = request.GET.get(constants.CARD_RANK)
    link_rating = request.GET.get(constants.CARD_LINK)
    pend_scale = request.GET.get(constants.CARD_PEND)

    has_search = (query and (card_type or level or rank or link_rating or pend_scale)) or query
    
    request.session['non_matches'] = request.session.get('non_matches', [])

    if has_search:
        filters = Q()
        words = query.strip().split()
        for word in words:
            filters &= Q(card_name__icontains=word)

        if request.session.get('non_matches') and request.session.get('latest_query') != request.META.get('HTTP_REFERER'):
            request.session['latest_query'] = request.get_full_path()
            request.session['non_matches'] = []
        
        results = CardInventory.objects.filter(filters).order_by('card_name')

        # Remove any prior non matches found (if any)
        non_matches = request.session.get('non_matches', [])
        if non_matches:
            ids_to_exclude = [card_id for card_id, card_name in non_matches]
            names_to_exclude = [card_name for card_id, card_name in non_matches]

            results = results.exclude(card_id__in=ids_to_exclude, card_name__in=names_to_exclude)

        # Slice the results to get the current page's records
        results_to_filter = results
        if (int(page_number) > 1):
            results_to_filter = results[page_size * (int(page_number) - 1):len(results)]

        filtered_cards = 0
        for inventory_card in results_to_filter:
            if filtered_cards >= 11:
                break
            if not inventory_card.card_data:
                card_data = fetch_card(inventory_card.card_id, inventory_card.card_name)
                if (filter_card_data(card_data, card_type, level, rank, link_rating, pend_scale)):
                    card_data.save()
                    inventory_card.card_data = card_data
                    inventory_card.save()
                    filtered_cards += 1
                else:
                    request.session['non_matches'] = request.session.get('non_matches', []) + [(card_data.card_id, card_data.card_name)]
            else:
                if (filter_card_data(inventory_card.card_data, card_type, level, rank, link_rating, pend_scale)):
                    filtered_cards += 1
                else:
                    request.session['non_matches'] = request.session.get('non_matches', []) + [(inventory_card.card_data.card_id, inventory_card.card_data.card_name)]

        non_matches = request.session.get('non_matches', [])

        # Remove the non-matches
        if non_matches:
            ids_to_exclude = [card_id for card_id, card_name in non_matches]
            names_to_exclude = [card_name for card_id, card_name in non_matches]
            results_to_filter = [
                card for card in results_to_filter 
                if card.card_id not in ids_to_exclude and card.card_name not in names_to_exclude
            ]

        if int(page_number) > 1:
            results = results[0:page_size * (int(page_number) - 1)] + results_to_filter
        else:
            results = results_to_filter

        paginator = Paginator(results, page_size)
        page_obj = paginator.get_page(page_number)

    return render(request, 'searcher.html', {
        'page_obj': page_obj,
        'query': query,
        constants.CARD_TYPE: card_type,
        constants.CARD_LEVEL: level,
        constants.CARD_RANK: rank,
        constants.CARD_LINK: link_rating,
        constants.CARD_PEND: pend_scale,
    })


@require_POST
def clear_card_data(request: HttpRequest):
    CardData.objects.all().delete()
    return redirect('/')
