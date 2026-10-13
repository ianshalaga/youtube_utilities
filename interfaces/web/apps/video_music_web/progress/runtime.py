from .job_progress import VideoMusicJobRegistry


# Shared registry for this Django process.
job_registry = VideoMusicJobRegistry()
