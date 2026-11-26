from django.urls import path

from .views import InferenceDetailView, InferenceListCreateView

urlpatterns = [
    path("", InferenceListCreateView.as_view(), name="inference-list-create"),
    path("<uuid:pk>/", InferenceDetailView.as_view(), name="inference-detail"),
]
