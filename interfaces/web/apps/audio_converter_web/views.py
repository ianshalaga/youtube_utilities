from django.shortcuts import render


def index(request):
    return render(request, "audio_converter_web/index.html")