import requests
from ..models import CardData, CardInventory
from django.db.models import Q
from yugisearcher import constants

def fetch_card(card_id: int, card_name: str):
    
    url = f"https://db.ygoresources.com/data/card/{card_id}"
    response = requests.get(url)
    data = response.json()
    

    # Get the card data
    card_data = data.get("cardData", {}).get("en", {})

    # Assign the data retrieved
    def check_empty(value):
        return None if value == '' else value

    card_name = check_empty(card_name)
    card_type = check_empty(card_data.get("cardType", "No Type"))
    defense = check_empty(card_data.get("def", None))
    card_effect = check_empty(card_data.get("effectText", ""))
    pend_effect = check_empty(card_data.get("pendulumEffectText", None))
    card_level = check_empty(card_data.get("level", None))
    card_rank = check_empty(card_data.get("rank", None))
    link_rating = check_empty(card_data.get("linkArrows", None))
    pend_scale = check_empty(card_data.get("pendulumScale", None))
    ban_status = check_empty(card_data.get("banlistStatus", None))
    image_link = CardData.get_artwork(card_id)
    
    return CardData(card_id=card_id, card_name=card_name, 
                                    card_type=card_type, defense=defense, 
                                    card_effect=card_effect, pend_effect=pend_effect,
                                    card_level=card_level, card_rank=card_rank,
                                    link_rating=link_rating, pend_scale=pend_scale,
                                    ban_status=ban_status, image_link=image_link)

def filter_card_data(card_data: CardData,
                     filter_type=None, filter_level=None,
                     filter_rank=None, filter_link=None,
                     filter_pend=None) -> bool:

    filter_parameters = {
        constants.CARD_TYPE: filter_type,
        constants.CARD_LEVEL: filter_level,
        constants.CARD_RANK: filter_rank,
        constants.CARD_LINK: filter_link,
        constants.CARD_PEND: filter_pend,
    }

    card_type = getattr(card_data, constants.CARD_TYPE, None).lower()

    if all(x not in (None, '') for x in (filter_type, filter_level, filter_rank, filter_link, filter_pend)):
        return True

    elif any(x not in (None, '') for x in (filter_level, filter_rank, filter_link, filter_pend)):
        if card_type != 'monster':
            return False

    for field, value in filter_parameters.items():
        if value not in (None, ''): # if a filter exists
            card_value = getattr(card_data, field, None)
                
            if card_value not in (None, ''): # if the card contains a value pertaining to the filter
                if check_if_integer(card_value) and check_if_integer(value):
                    if int(card_value) != int(value):
                        return False

                elif card_value.lower() != value.lower():
                    return False
            else:
                return False
    return True

def check_if_integer(value):
    try:
        int(value)
        return True
    except (ValueError, TypeError):
        return False


