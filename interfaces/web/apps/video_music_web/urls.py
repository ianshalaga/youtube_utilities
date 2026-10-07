from django.urls import path

from . import views


app_name = "video_music"

urlpatterns = [
    path("", views.index, name="index"),
]