from django.urls import path

from . import views


app_name = "video_joiner"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
]