from django.urls import path

from . import views


app_name = "audio_converter"

urlpatterns = [
    path("", views.index, name="index"),
]