from django.db import models
class CardArtwork(models.Model):
    card_id = models.BigIntegerField(primary_key=True, null=False)
    artwork_path = models.TextField(null=False, blank=False)

    class Meta:
        db_table = 'card_artwork'

    def __str__(self):
        return self.artwork_path

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
