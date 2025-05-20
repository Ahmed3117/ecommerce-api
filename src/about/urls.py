from django.urls import path
from .views import *
urlpatterns = [
    # FAQs
    path('faqs/', FAQListCreateAPIView.as_view(), name='faq-list-create'),
    path('faqs/<int:pk>/', FAQRetrieveUpdateDestroyAPIView.as_view(), name='faq-detail'),
    path('faqs_list/', FAQListAPIView.as_view(), name='faq-list-create'), #for customers
    
]

