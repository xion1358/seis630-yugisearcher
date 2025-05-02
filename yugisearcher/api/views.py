import io
import json
import os
import shutil
import time
import zipfile
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
from django.core.management import call_command


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

from django.core.cache import cache

PROGRESS_KEY = 'card_data_retrieval_progress'

def set_progress(progress):
    cache.set(PROGRESS_KEY, progress, timeout=300)

# This is what well see in the console. Note that the number seen in the console is the total bytes of the message body
# {"progress":0} (14 bytes)
# {"progress":10} (16 bytes)
# {"progress":100} (17 bytes)
def get_progress(request):
    progress = cache.get(PROGRESS_KEY, 0)
    return JsonResponse({'progress': progress})

@require_POST
def retrieve_card_data(request):
    set_progress(1)
    results = {}

    # Download
    download_successful = download_all_card_data()
    results['download'] = 'success' if download_successful else 'failed'

    # Import
    if download_successful:
        import_successful = import_downloaded_card_data("yugioh-card-history-main/en")
        results['import'] = 'success' if import_successful else 'failed'

        # Cleanup
        cleanup_successful = cleanup_download_directory("yugioh-card-history-main")
        results['cleanup'] = 'success' if cleanup_successful else 'failed'

    else:
        results['import'] = 'skipped'
        cleanup_download_directory("yugioh-card-history-main")
        results['cleanup'] = 'attempted'

    return JsonResponse(results, status=200 if all(v == 'success' for k, v in results.items()) else 500)

def download_all_card_data():
    url = "https://github.com/db-ygoresources-com/yugioh-card-history/archive/refs/heads/main.zip"
    output_dir = "yugioh-card-history-main"
    zip_file = "yugioh-card-history-main.zip"

    try:
        response = requests.get(url, stream=True, allow_redirects=True)
        response.raise_for_status()

        total_size = int(response.headers.get('Content-Length', 0))
        bytes_downloaded = 0

        if os.path.exists(zip_file):
            os.remove(zip_file)
        if response.status_code == 200:
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            os.makedirs(output_dir)
            with open(zip_file, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        bytes_downloaded += len(chunk)
                        # print(f"total size: {total_size}")
                        if total_size > 0:
                            progress = int((bytes_downloaded / total_size) * 33)
                            set_progress(progress)
            print(f"Repository downloaded to yugioh-card-history-main.zip")
            with zipfile.ZipFile(zip_file) as zip_ref:
                zip_ref.extractall(".")
            os.remove(zip_file)
            print(f"Repository extracted to {output_dir}/")
            return True
        else:
            print(f"Failed to download repo: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error during download: {e}")
        return False

def import_downloaded_card_data(directory):
    json_files = [f for f in os.listdir(directory) if f.endswith('.json')]
    total_files = len(json_files)
    imported_count = 0

    for i, file in enumerate(json_files):
        file_path = os.path.join(directory, file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            card_id = data.get('id')
            card_name = data.get('name', 'No Name')
            card_type = data.get('type', 'No Type')
            defense = data.get('def', None)
            card_effect = data.get('effectText', '')
            pend_effect = data.get('pendEffect', '')
            card_level = data.get('level', None)
            card_rank = data.get('rank', None)
            link_rating = data.get('linkRating', None)
            pend_scale = data.get('pendScale', None)
            ban_status = data.get('banStatus', None)
            image_link = data.get('imageLink', None)

            card_data, created = CardData.objects.update_or_create(
                card_id=card_id,
                defaults={
                    'card_name': card_name,
                    'card_type': card_type,
                    'defense': defense,
                    'card_effect': card_effect,
                    'pend_effect': pend_effect,
                    'card_level': card_level,
                    'card_rank': card_rank,
                    'link_rating': link_rating,
                    'pend_scale': pend_scale,
                    'ban_status': ban_status,
                    'image_link': CardArtwork.objects.filter(card_id=card_id).first().artwork_path
                }
            )

            CardInventory.objects.update_or_create(
                card_id=card_id,
                card_name=card_name,
                defaults={'card_data': card_data}
            )

            imported_count += 1
            progress = int(33 + ((imported_count / total_files) * 33))
            set_progress(progress)

            if created:
                print(f"Created new card: {card_name}")
            else:
                print(f"Updated existing card: {card_name}")

        except Exception as e:
            print(f"Error importing {file}: {e}")
            return False
    return True

def cleanup_download_directory(directory):
    try:
        shutil.rmtree(directory)
        print(f"Deleted directory: {directory}")
        set_progress(100)
        time.sleep(3)
        return True
    except OSError as e:
        print(f"Error deleting directory {directory}: {e}")
        return False
    
def import_card_artwork(request):
    if request.method == 'POST':
        try:
            call_command('import_artworks', force=True)
            return JsonResponse({'status': 'success', 'message': 'Card artwork import started.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request.'})