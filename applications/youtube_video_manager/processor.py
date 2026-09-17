


class YouTubeVideoManagerProcessor:
    def process(self) -> None:
        job = self._job_repository.find_pending()

        if job is not None:
            self._logger.info("Continuing pending job.")
        else:
            self._logger.info("Creating new job.")

            manifest = self._manifest_reader.read(...)
            youtube_videos = self._youtube_discovery.discover()
            album = self._album_builder.build(
                manifest,
                youtube_videos,
            )
            job = self._planner.plan(album)

        self._updater.update(job)