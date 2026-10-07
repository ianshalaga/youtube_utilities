from django.shortcuts import render
from django.views import View


class IndexView(View):

    def get(self, request, *args, **kwargs):
        return render(
            request,
            "video_joiner_web/index.html",
        )