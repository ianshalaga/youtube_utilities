from django.shortcuts import render


def index(request):
    return render(request, "video_joiner_web/index.html")