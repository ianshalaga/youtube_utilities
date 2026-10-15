from django.urls import path

from .views import FileBrowserSelectionView, FileBrowserView

app_name = "file_browser"

urlpatterns = [
    path("", FileBrowserView.as_view(), name="browse"),
    path(
        "select/",
        FileBrowserSelectionView.as_view(),
        name="select",
    ),
]
