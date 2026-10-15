document.addEventListener("DOMContentLoaded", () => {
  const pickerButtons = document.querySelectorAll("[data-file-picker]");
  const browserPanel = document.getElementById("file-browser-panel");
  const closeButton = document.getElementById("file-browser-close");
  const description = document.getElementById("file-browser-description");

  if (!browserPanel || !closeButton || !description) {
    console.error("No se encontró el panel del navegador de archivos.");
    return;
  }

  const allowedTargets = {
    audios_dir: "audios",
    video_path: "video",
  };

  let activeField = null;

  function openBrowser(fieldName) {
    const target = allowedTargets[fieldName];

    if (!target) {
      return;
    }

    activeField = fieldName;

    description.textContent =
      target === "audios"
        ? "Selecciona el directorio que contiene las canciones."
        : "Selecciona el archivo de vídeo base.";

    browserPanel.dataset.target = target;
    browserPanel.hidden = false;
    browserPanel.classList.remove("hidden");

    browserPanel.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });

    window.dispatchEvent(
      new CustomEvent("file-browser-open", {
        detail: { target },
      }),
    );
  }

  function closeBrowser() {
    browserPanel.hidden = true;
    browserPanel.classList.add("hidden");
    activeField = null;
  }

  pickerButtons.forEach((button) => {
    button.addEventListener("click", () => {
      openBrowser(button.dataset.filePicker);
    });
  });

  closeButton.addEventListener("click", closeBrowser);

  window.addEventListener("file-browser-selected", (event) => {
    const { target, path } = event.detail || {};

    if (
      !activeField ||
      allowedTargets[activeField] !== target ||
      typeof path !== "string" ||
      !path
    ) {
      return;
    }

    const field = document.getElementById(`id_${activeField}`);

    if (!field) {
      console.error(`No se encontró el campo id_${activeField}.`);
      return;
    }

    field.value = path;
    field.dispatchEvent(new Event("input", { bubbles: true }));
    field.dispatchEvent(new Event("change", { bubbles: true }));

    closeBrowser();
    field.focus();
  });
});
