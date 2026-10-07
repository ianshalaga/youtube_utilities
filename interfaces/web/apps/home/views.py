from django.shortcuts import render

from .catalog import APPLICATIONS


def index(request):
    context = {
        "applications": APPLICATIONS,
    }

    return render(
        request,
        "home/index.html",
        context,
    )