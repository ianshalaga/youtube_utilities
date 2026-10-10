from django.contrib import messages
from django.shortcuts import redirect, render
from django.views import View

from core.config_manager import ConfigManager

from .forms import VideoMusicForm


class IndexView(View):
    template_name = "video_music_web/index.html"

    def get(self, request, *args, **kwargs):
        config = ConfigManager()

        form = VideoMusicForm(
            initial={
                "max_items_per_dir": config.video_music_max_items_per_dir,
                "audios_dir": config.video_music_default_audios_dir,
                "video_path": config.video_music_default_video_path,
                "output_dir": config.video_music_default_output_dir,
            }
        )

        return render(
            request,
            self.template_name,
            {"form": form},
        )

    def post(self, request, *args, **kwargs):
        form = VideoMusicForm(request.POST)

        if not form.is_valid():
            return render(
                request,
                self.template_name,
                {"form": form},
            )

        config = ConfigManager()
        config.update_video_music_defaults(
            max_items_per_dir=form.cleaned_data["max_items_per_dir"],
            default_audios_dir=form.cleaned_data["audios_dir"],
            default_video_path=form.cleaned_data["video_path"],
            default_output_dir=form.cleaned_data["output_dir"],
        )

        messages.success(
            request,
            "Los valores predeterminados se guardaron correctamente.",
        )

        return redirect("video_music:index")
