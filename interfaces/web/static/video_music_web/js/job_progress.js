(() => {
  const config = document.getElementById("job-progress-config");
  const statusUrl = config.dataset.statusUrl;

  const elements = {
    status: document.getElementById("job-status"),
    message: document.getElementById("job-message"),
    error: document.getElementById("job-error"),
    currentDirectory: document.getElementById("current-directory"),
    totalDirectories: document.getElementById("total-directories"),
    completedTracks: document.getElementById("completed-tracks"),
    totalTracks: document.getElementById("total-tracks"),
    runningTracks: document.getElementById("running-tracks"),
    failedTracks: document.getElementById("failed-tracks"),
    trackList: document.getElementById("track-list"),
    noTracks: document.getElementById("no-tracks"),
  };

  const terminalStatuses = new Set(["completed", "failed"]);
  const pollIntervalMs = 1000;
  const maxRetryDelayMs = 15000;
  const requestTimeoutMs = 10000;
  let timerId = null;
  let pollingStopped = false;
  let retryDelayMs = pollIntervalMs;

  function setText(element, value) {
    if (element) {
      element.textContent = value ?? "";
    }
  }

  function updateTracks(tracks) {
    if (!elements.trackList && tracks.length === 0) {
      return;
    }

    if (!elements.trackList) {
      const list = document.createElement("ul");
      list.id = "track-list";
      elements.noTracks?.replaceWith(list);
      elements.trackList = list;
      elements.noTracks = null;
    }

    const fragment = document.createDocumentFragment();

    for (const track of tracks) {
      const item = document.createElement("li");
      const name = document.createElement("strong");

      name.textContent = track.name || "Pista";
      item.append(name);
      item.append(
        document.createTextNode(` — ${track.status} — ${track.message}`),
      );

      if (track.duration) {
        item.append(document.createTextNode(` (${track.duration})`));
      }

      if (track.error_message) {
        const error = document.createElement("p");
        error.textContent = `Error: ${track.error_message}`;
        item.append(error);
      }

      fragment.append(item);
    }

    elements.trackList.replaceChildren(fragment);
  }

  function updatePage(job) {
    setText(elements.status, job.status);
    setText(elements.message, job.message);
    setText(elements.currentDirectory, job.current_directory);
    setText(elements.totalDirectories, job.total_directories);
    setText(elements.completedTracks, job.completed_tracks);
    setText(elements.totalTracks, job.total_tracks);
    setText(elements.runningTracks, job.running_tracks);
    setText(elements.failedTracks, job.failed_tracks);

    if (job.error_message) {
      if (!elements.error) {
        const error = document.createElement("p");
        error.id = "job-error";
        error.className = "whitespace-pre-wrap break-words";
        const label = document.createElement("strong");
        label.textContent = "Error:";
        error.append(label, document.createTextNode(" "));
        error.append(document.createTextNode(job.error_message));
        elements.message.after(error);
        elements.error = error;
      } else {
        elements.error.replaceChildren();
        const label = document.createElement("strong");
        label.textContent = "Error:";
        elements.error.append(
          label,
          document.createTextNode(` ${job.error_message}`),
        );
      }
    }

    updateTracks(job.tracks || []);

    if (terminalStatuses.has(job.status)) {
      stopPolling();
      const resultsUrl = new URL("/video-music/", window.location.origin);
      resultsUrl.searchParams.set("job_id", job.job_id);
      window.location.assign(resultsUrl.toString());
    }
  }

  function stopPolling() {
    pollingStopped = true;

    if (timerId !== null) {
      window.clearTimeout(timerId);
      timerId = null;
    }
  }

  async function refreshProgress() {
    const controller = new AbortController();
    const requestTimeoutId = window.setTimeout(
      () => controller.abort(),
      requestTimeoutMs,
    );

    try {
      const response = await fetch(statusUrl, {
        headers: { Accept: "application/json" },
        cache: "no-store",
        signal: controller.signal,
      });

      if (!response.ok) {
        throw new Error(`Error al consultar el trabajo: ${response.status}`);
      }

      const data = await response.json();
      retryDelayMs = pollIntervalMs;
      updatePage(data.job);
    } catch (error) {
      setText(
        elements.message,
        error.name === "AbortError"
          ? "La consulta de progreso tardó demasiado. Se volverá a intentar."
          : "No se pudo actualizar el progreso. Se volverá a intentar.",
      );
      console.error(error);
      retryDelayMs = Math.min(retryDelayMs * 2, maxRetryDelayMs);
    } finally {
      window.clearTimeout(requestTimeoutId);

      if (!pollingStopped) {
        timerId = window.setTimeout(refreshProgress, retryDelayMs);
      }
    }
  }

  refreshProgress();
})();
