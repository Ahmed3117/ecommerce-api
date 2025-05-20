
from rest_framework import generics
from django_filters.rest_framework import DjangoFilterBackend
import rest_framework.filters as rest_filters
from about.models import FAQ
from about.serializers import FAQSerializer


class FAQListAPIView(generics.ListAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    filter_backends = [DjangoFilterBackend, rest_filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['title', 'description']

#^ < ==========================Dashboard endpoints========================== >

class FAQListCreateAPIView(generics.ListCreateAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    filter_backends = [DjangoFilterBackend, rest_filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['title', 'description']

class FAQRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = FAQ.objects.all()
    serializer_class = FAQSerializer
    






