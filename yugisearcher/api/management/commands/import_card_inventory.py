import os
import requests
from django.core.management.base import BaseCommand
from api.models import CardInventory

REVISION_FILE_PATH = 'last_known_revision.txt'

# This command will check for the last known revision of the API data and if 
# there is a difference will update the changed card inventory data,
# and by extension delete card data associated with the card inventory data
class Command(BaseCommand):
    help = 'Fetches card data into the inventory database'    

    def handle(self, *args, **kwargs):
        api_url = "https://db.ygoresources.com/data/idx/card/name/en"
        manifest_url = "https://db.ygoresources.com/manifest/"

        last_known_revision = self.get_last_known_revision()

        try:
            response = requests.get(api_url)
            response.raise_for_status()
            data = response.json()
            existing_cards = CardInventory.objects.all()

            if not data:
                self.stdout.write(self.style.WARNING('No card data received from the API.'))
                return

            current_revision = response.headers.get('X-Cache-Revision')

            if current_revision == last_known_revision and existing_cards.exists():
                self.stdout.write(self.style.SUCCESS('No new revision found'))
                return
            if current_revision != last_known_revision and existing_cards.exists():
                manifest_response = requests.get(f"{manifest_url}{current_revision}")
                manifest_response.raise_for_status()
                changes = manifest_response.json()

                if not changes or 'data' not in changes or 'card' not in changes['data']:
                    self.stdout.write(self.style.WARNING('No changes found in the manifest or invalid data.'))
                    self.update_revision(current_revision)
                    return

                changed_card_ids = set(changes['data']['card'].keys())

                # Use django ORM to delete the changed cards that have matching ids in the changed revision
                # DELETE FROM card_inventory
                # WHERE card_id IN (changed_card_ids);
                CardInventory.objects.filter(card_id__in=changed_card_ids).delete()

            for card_name, card_ids in data.items():
                card_id = card_ids[0]
                CardInventory.objects.get_or_create(card_id=card_id, card_name=card_name)
            
            self.update_revision(current_revision)

            self.stdout.write(self.style.SUCCESS('Successfully fetched and inserted card data'))

        except requests.exceptions.RequestException as e:
            self.stdout.write(self.style.ERROR(f"Error fetching data from API: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
    

    def get_last_known_revision(self):
        if os.path.exists(REVISION_FILE_PATH):
            with open(REVISION_FILE_PATH, 'r') as file:
                return file.read().strip()
        else:
            return "0"

    def update_revision(self, new_revision):
        with open(REVISION_FILE_PATH, 'w') as file:
            file.write(str(new_revision))
