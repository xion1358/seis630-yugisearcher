from django.core.management.base import BaseCommand
from api.models import CardArtwork
import requests

class Command(BaseCommand):
    help = 'Fetch and store artwork paths for all cards from the manifest'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update: delete existing entries and reload everything.'
        )

    def handle(self, *args, **options):
        force_update = options['force']

        if CardArtwork.objects.exists():
            if not force_update:
                self.stdout.write(self.style.SUCCESS(
                    "CardArtwork table already has data. Skipping import. Use --force to delete and reload."))
                return
            else:
                self.stdout.write("Force flag detected. Deleting existing CardArtwork entries...")
                CardArtwork.objects.all().delete()

        manifest_url = 'https://artworks.ygoresources.com/manifest.json'
        try:
            self.stdout.write("Downloading artwork manifest...")
            manifest = requests.get(manifest_url).json()
            cards = manifest.get("cards", {})
            updated = 0
            skipped = 0

            for card_id_str, versions in cards.items():
                try:
                    card_id = int(card_id_str)
                    first_version = next(iter(versions.values()))
                    en_artworks = first_version.get('idx', {}).get('en', [])
                    artwork_path = None

                    if en_artworks:
                        artwork_path = en_artworks[0].get('path')

                    if not artwork_path:
                        artwork_path = first_version.get('bestTCG') or first_version.get('bestArt')

                    if artwork_path:
                        CardArtwork.objects.update_or_create(
                            card_id=card_id,
                            defaults={'artwork_path': artwork_path}
                        )
                        updated += 1
                    else:
                        self.stdout.write(self.style.WARNING(f"No artwork found for card {card_id}"))
                        skipped += 1
                except Exception as e:
                    self.stderr.write(f"Error processing card {card_id_str}: {e}")
                    skipped += 1

            self.stdout.write(self.style.SUCCESS(f"Artwork import complete. {updated} cards updated, {skipped} skipped."))

        except requests.exceptions.RequestException as e:
            self.stderr.write(f"Error fetching manifest: {e}")
