from django.db import models
import requests

# Create your models here.
class CardData(models.Model):
    # No primary key specified. Django automatically creates an id column for the primary key which is auto generated
    card_id = models.BigIntegerField(null=False)
    card_name = models.CharField(max_length=255, null=False, blank=False, default="No Name")
    card_type = models.CharField(max_length=255, null=False, blank=False, default="No Type")
    defense = models.IntegerField(null=True, blank=True)
    card_effect = models.TextField(null=True, blank=True)
    pend_effect = models.TextField(null=True, blank=True)
    card_level = models.IntegerField(null=True, blank=True)
    card_rank = models.IntegerField(null=True, blank=True)
    link_rating = models.IntegerField(null=True, blank=True)
    pend_scale = models.IntegerField(null=True, blank=True)
    ban_status = models.IntegerField(null=True, blank=True)
    image_link = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'card_data'
        unique_together = ('card_id', 'card_name')

    def __str__(self):
        return str(self.card_name)
    
    @staticmethod
    def get_artwork(card_id):
        manifest_url = 'https://artworks.ygoresources.com/manifest.json'
        try:
            manifest = requests.get(manifest_url).json()
            card_data = manifest.get("cards", {}).get(str(card_id), None)
            if card_data:
                art_id = list(card_data.keys())[0]
                artwork_data = card_data[art_id]
                artwork_path = artwork_path = artwork_data.get('bestTCG') or artwork_data.get('bestArt') or ''
                artwork_url = f'{artwork_path}'
                
                return artwork_url
            else:
                return None
        except requests.exceptions.RequestException as e:
            print(f"Error fetching manifest: {e}")
            return None

    
class CardInventory(models.Model):
    # No primary key specified. Django automatically creates an id column for the primary key which is auto generated
    card_id = models.BigIntegerField(null=False)
    card_name = models.CharField(max_length=255, null=False, blank=False, default="No Name")

    card_data = models.ForeignKey(CardData, on_delete=models.SET_NULL, related_name="inventories", null=True, blank=True)

    class Meta:
        db_table = 'card_inventory'
        unique_together = ('card_id', 'card_name')

    def __str__(self):
        return self.card_name
