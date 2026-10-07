from django.shortcuts import render
from django.views import View

from .catalog import APPLICATIONS


class IndexView(View):
    def get(self, request, *args, **kwargs):
        context = {
            "applications": APPLICATIONS,
        }

        return render(
            request,
            "home/index.html",
            context,
        )