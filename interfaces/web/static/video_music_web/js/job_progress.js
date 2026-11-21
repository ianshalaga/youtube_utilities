(() => {
  const config = document.getElementById("job-progress-config");
  const statusUrl = config.dataset.statusUrl;
  const resultUrl = config.dataset.resultUrl;

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
  const jobStatusPresentation = {
    queued: {
      label: "En espera",
      emoji: "⏳",
      color: "border-gray-500/40 bg-gray-950/50 text-gray-300",
    },
    running: {
      label: "En procesamiento",
      emoji: "🔄",
      color: "border-blue-500/40 bg-blue-950/50 text-blue-300",
    },
    completed: {
      label: "Completado",
      emoji: "✅",
      color: "border-green-500/40 bg-green-950/50 text-green-300",
    },
    failed: {
      label: "Fallido",
      emoji: "❌",
      color: "border-red-500/40 bg-red-950/50 text-red-300",
    },
  };
  const trackStatusPresentation = {
    pending: { label: "Pendiente", emoji: "⏳", color: "text-gray-400" },
    running: {
      label: "En procesamiento",
      emoji: "🔄",
      color: "text-blue-300",
    },
    completed: { label: "Completada", emoji: "✅", color: "text-green-300" },
    failed: { label: "Fallida", emoji: "❌", color: "text-red-300" },
  };
  const defaultTrackMessages = {
    pending: "Pendiente",
    running: "Procesando",
    completed: "Completada",
    failed: "Fallida",
  };
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
    const orderedTracks = [...tracks].sort(
      (left, right) =>
        Number(left.status === "completed") -
        Number(right.status === "completed"),
    );

    for (const track of orderedTracks) {
      const item = document.createElement("li");
      const name = document.createElement("strong");
      const presentation = trackStatusPresentation[track.status] || {
        label: "Estado desconocido",
        emoji: "ℹ️",
        color: "text-gray-400",
      };
      const status = document.createElement("div");

      name.textContent = track.name || "Pista";
      name.className = "text-white";
      status.className =
        `flex flex-wrap items-center gap-2 text-sm font-semibold ${presentation.color}`;
      status.textContent = `${presentation.emoji} ${presentation.label}`;
      status.append(
        document.createTextNode(" | "),
        name,
      );
      item.append(status);

      if (
        track.message &&
        track.message !== defaultTrackMessages[track.status] &&
        (!track.duration || !track.message.startsWith("Duración detectada:"))
      ) {
        const activity = document.createElement("p");
        activity.className = "mt-1 text-sm text-gray-400";
        activity.textContent = track.message;
        item.append(activity);
      }

      if (track.duration) {
        status.append(
          document.createTextNode(" | "),
          Object.assign(document.createElement("span"), {
            className: "text-indigo-300",
            textContent: track.duration,
          }),
        );
      }

      if (track.error_message) {
        const error = document.createElement("p");
        error.className = "mt-1 text-sm text-red-400";
        error.textContent = `Error: ${track.error_message}`;
        item.append(error);
      }

      fragment.append(item);
    }

    elements.trackList.replaceChildren(fragment);
  }

  function updatePage(job) {
    const status = jobStatusPresentation[job.status] || {
      label: "Estado desconocido",
      emoji: "ℹ️",
      color: "border-gray-500/40 bg-gray-950/50 text-gray-300",
    };
    setText(elements.status, `${status.emoji} ${status.label}`);
    elements.status.className =
      `ml-1 inline-flex rounded-full border px-3 py-1 text-sm font-bold ${status.color}`;
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
      window.location.assign(resultUrl);
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
