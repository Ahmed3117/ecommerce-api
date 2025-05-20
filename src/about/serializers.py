from rest_framework import serializers
from about.models import FAQ

#------------- FAQ -------------#


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'
