from dataclasses import asdict
from pathlib import Path
from threading import Thread

from django.contrib import messages
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.views import View

from applications.video_music.input import VideoMusicInput
from core.config_manager import ConfigManager

from .forms import VideoMusicForm
from .progress.job_runner import run_video_music_job
from .progress.runtime import job_registry


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

        return self._process_video_music(request, form)

    
    def _process_video_music(self, request, form):
        config = ConfigManager()
        cleaned_data = form.cleaned_data

        # Persist the submitted values before starting the job.
        config.update_video_music_defaults(
            max_items_per_dir=cleaned_data["max_items_per_dir"],
            default_audios_dir=cleaned_data["audios_dir"],
            default_video_path=cleaned_data["video_path"],
            default_output_dir=cleaned_data["output_dir"],
        )

        audios_dir = Path(cleaned_data["audios_dir"])
        output_dir = Path(cleaned_data["output_dir"])

        # Resolve relative output paths against the audio directory.
        if not output_dir.is_absolute():
            output_dir = audios_dir / output_dir

        input_data = VideoMusicInput(
            max_items_per_dir=cleaned_data["max_items_per_dir"],
            audios_dir=audios_dir,
            video_path=Path(cleaned_data["video_path"]),
            output_dir=output_dir,
        )

        # Register the job before starting its execution.
        job_id = job_registry.create_job(
            video_path=input_data.video_path,
            audios_dir=input_data.audios_dir,
            output_dir=input_data.output_dir,
            max_items_per_dir=input_data.max_items_per_dir,
        )

        # Execute the job outside the HTTP request.
        thread = Thread(
            target=run_video_music_job,
            args=(job_id, input_data),
            daemon=True,
        )
        thread.start()

        messages.success(
            request,
            "El trabajo se ha iniciado correctamente.",
        )

        return redirect(
            "video_music:job_progress",
            job_id=job_id,
        )


class JobProgressView(View):
    """Render the page used to monitor a Video Music job."""

    template_name = "video_music_web/job_progress.html"

    def get(self, request, job_id, *args, **kwargs):
        job = job_registry.get_job(job_id)

        if job is None:
            raise Http404("No existe un trabajo con ese identificador.")

        return render(
            request,
            self.template_name,
            {"job": job},
        )


class JobStatusView(View):
    """Expose the current state of a Video Music job as JSON."""

    def get(self, request, job_id, *args, **kwargs):
        job = job_registry.get_job(job_id)

        if job is None:
            raise Http404("No existe un trabajo con ese identificador.")

        return JsonResponse({"job": asdict(job)})
