document.addEventListener("DOMContentLoaded", () => {
  const drivesButton = document.getElementById("file-browser-drives");
  const parentButton = document.getElementById("file-browser-parent");
  const refreshButton = document.getElementById("file-browser-refresh");
  const pathInput = document.getElementById("file-browser-path");
  const selectedPathInput = document.getElementById(
    "file-browser-selected-path",
  );
  const statusElement = document.getElementById("file-browser-status");
  const entriesList = document.getElementById("file-browser-entries");
  const confirmButton = document.getElementById("file-browser-confirm");

  if (
    !drivesButton ||
    !parentButton ||
    !refreshButton ||
    !pathInput ||
    !selectedPathInput ||
    !statusElement ||
    !entriesList ||
    !confirmButton
  ) {
    return;
  }

  const browserUrl = "/file-browser/";
  const selectionUrl = "/file-browser/select/";

  let activeTarget = null;

  let currentPath = "";
  let selectedEntry = null;

  async function requestJson(url, options = {}) {
    const response = await fetch(url, options);
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      throw new Error(data.error || `Error HTTP ${response.status}`);
    }

    return data;
  }

  function setStatus(message) {
    statusElement.textContent = message;
  }

  function clearSelection() {
    selectedEntry = null;
    selectedPathInput.value = "";
    confirmButton.disabled = true;
  }

  function clearEntries() {
    entriesList.replaceChildren();
  }

  function renderEntries(entries) {
    clearEntries();

    if (entries.length === 0) {
      const item = document.createElement("li");
      item.className = "rounded-lg p-4 text-center text-gray-400";
      item.textContent = "No hay elementos para mostrar.";
      entriesList.appendChild(item);
      return;
    }

    for (const entry of entries) {
      const item = document.createElement("li");
      item.className =
        "flex flex-wrap items-center gap-2 rounded-lg p-2 " +
        "transition-colors hover:bg-slate-800";

      const isDirectory = entry.type === "directory" || entry.type === "drive";

      const openButton = document.createElement("button");
      openButton.type = "button";
      openButton.className =
        "min-w-0 flex-1 rounded-lg border border-transparent " +
        "px-3 py-2 text-left font-semibold text-gray-200 " +
        "transition-colors hover:bg-slate-700 " +
        "focus-visible:outline-2 focus-visible:outline-offset-2 " +
        "focus-visible:outline-green-500";
      openButton.textContent = `${isDirectory ? "📁" : "📄"} ${entry.name}`;

      openButton.addEventListener("click", () => {
        if (isDirectory) {
          openDirectory(entry.path);
        } else {
          selectEntry(entry);
        }
      });

      item.appendChild(openButton);

      if (entry.type !== "drive") {
        const selectButton = document.createElement("button");
        selectButton.type = "button";
        selectButton.className =
          "shrink-0 rounded-lg border border-indigo-500/50 " +
          "bg-indigo-950/40 px-3 py-2 text-sm font-bold " +
          "text-indigo-200 transition-colors " +
          "hover:border-indigo-400 hover:bg-indigo-900/60 " +
          "focus-visible:outline-2 focus-visible:outline-offset-2 " +
          "focus-visible:outline-green-500";
        selectButton.textContent = "Seleccionar";

        selectButton.addEventListener("click", () => {
          selectEntry(entry);
        });

        item.appendChild(selectButton);
      }

      entriesList.appendChild(item);
    }
  }

  async function loadDrives() {
    clearSelection();
    clearEntries();
    setStatus("Cargando unidades…");

    try {
      const data = await requestJson(`${browserUrl}?action=drives`);

      currentPath = "";
      pathInput.value = "";
      parentButton.disabled = true;
      refreshButton.disabled = true;

      renderEntries(data.entries || []);
      setStatus("Selecciona una unidad para explorarla.");
    } catch (error) {
      setStatus(`Error al cargar las unidades: ${error.message}`);
    }
  }

  async function loadDefaultLocation(target) {
    clearSelection();
    clearEntries();
    setStatus("Cargando ubicación predeterminada…");

    try {
      const params = new URLSearchParams({
        action: "default",
        target,
      });

      const data = await requestJson(`${browserUrl}?${params.toString()}`);

      currentPath = data.path;
      pathInput.value = currentPath;

      parentButton.disabled = false;
      refreshButton.disabled = false;

      renderEntries(data.entries || []);
      setStatus(
        `Ubicación predeterminada cargada. ` +
          `${(data.entries || []).length} elemento(s) encontrado(s).`,
      );
    } catch (error) {
      setStatus(
        `Error al cargar la ubicación predeterminada: ${error.message}`,
      );
    }
  }

  async function openDirectory(path) {
    clearSelection();
    clearEntries();
    setStatus("Cargando directorio…");

    try {
      const params = new URLSearchParams({
        action: "list",
        path: path,
      });

      const data = await requestJson(`${browserUrl}?${params.toString()}`);

      currentPath = data.path || path;
      pathInput.value = currentPath;

      parentButton.disabled = false;
      refreshButton.disabled = false;

      renderEntries(data.entries || []);
      setStatus(`${(data.entries || []).length} elemento(s) encontrado(s).`);
    } catch (error) {
      setStatus(`Error al abrir el directorio: ${error.message}`);
    }
  }

  function getParentPath(path) {
    // En Windows, la unidad raíz debe conservarse como C:\.
    if (/^[a-zA-Z]:[\\/]*$/.test(path)) {
      return null;
    }

    // En otros sistemas, la raíz es /.
    if (path === "/") {
      return null;
    }

    const trimmed = path.replace(/[\\/]+$/, "");
    const separatorIndex = Math.max(
      trimmed.lastIndexOf("\\"),
      trimmed.lastIndexOf("/"),
    );

    if (separatorIndex < 0) {
      return null;
    }

    // Conserva la barra final de la raíz de una unidad Windows.
    if (separatorIndex === 2 && /^[a-zA-Z]:/.test(trimmed)) {
      return trimmed.slice(0, 3);
    }

    if (separatorIndex === 0) {
      return "/";
    }

    return trimmed.slice(0, separatorIndex);
  }

  function selectEntry(entry) {
    selectedEntry = entry;
    selectedPathInput.value = entry.path;
    confirmButton.disabled = false;
    setStatus(`Seleccionado: ${entry.name}`);
  }

  async function confirmSelection() {
    if (!selectedEntry) {
      return;
    }

    confirmButton.disabled = true;
    setStatus("Validando selección…");

    try {
      const body = new URLSearchParams({
        path: selectedEntry.path,
        type: selectedEntry.type,
      });

      const csrfInput = document.querySelector("[name=csrfmiddlewaretoken]");

      const headers = {
        "Content-Type": "application/x-www-form-urlencoded",
      };

      if (csrfInput) {
        headers["X-CSRFToken"] = csrfInput.value;
      }

      const data = await requestJson(selectionUrl, {
        method: "POST",
        headers,
        body,
        credentials: "same-origin",
      });

      selectedEntry = data.selection;
      selectedPathInput.value = data.selection.path;
      setStatus("Selección validada correctamente.");

      const expectedType = activeTarget === "audios" ? "directory" : "file";

      if (data.selection.type !== expectedType) {
        confirmButton.disabled = false;

        setStatus(
          activeTarget === "audios"
            ? "Debes seleccionar un directorio de canciones."
            : "Debes seleccionar un archivo de vídeo.",
        );

        return;
      }

      window.dispatchEvent(
        new CustomEvent("file-browser-selected", {
          detail: {
            target: activeTarget,
            path: data.selection.path,
          },
        }),
      );
    } catch (error) {
      confirmButton.disabled = false;
      setStatus(`Error al validar la selección: ${error.message}`);
    }
  }

  window.addEventListener("file-browser-open", (event) => {
    const target = event.detail?.target;

    if (!["audios", "video"].includes(target)) {
      return;
    }

    activeTarget = target;
    loadDefaultLocation(target);
  });

  drivesButton.addEventListener("click", loadDrives);

  parentButton.addEventListener("click", () => {
    const parentPath = getParentPath(currentPath);

    if (parentPath === null) {
      loadDrives();
    } else {
      openDirectory(parentPath);
    }
  });

  refreshButton.addEventListener("click", () => {
    if (currentPath) {
      openDirectory(currentPath);
    }
  });

  confirmButton.addEventListener("click", confirmSelection);
});
