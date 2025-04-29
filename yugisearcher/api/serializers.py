from rest_framework import serializers
from .models import CardData

class CardDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardData
        fields = '__all__'