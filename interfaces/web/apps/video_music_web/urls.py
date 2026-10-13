from django.urls import path
from . import views

app_name = "video_music"

urlpatterns = [
    path("", views.IndexView.as_view(), name="index"),
    path(
        "jobs/<str:job_id>/",
        views.JobProgressView.as_view(),
        name="job_progress",
    ),
    path(
        "jobs/<str:job_id>/status/",
        views.JobStatusView.as_view(),
        name="job_status",
    ),
]