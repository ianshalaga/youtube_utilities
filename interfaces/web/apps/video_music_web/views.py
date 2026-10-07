from django.shortcuts import render


def index(request):
    return render(request, "video_music_web/index.html")