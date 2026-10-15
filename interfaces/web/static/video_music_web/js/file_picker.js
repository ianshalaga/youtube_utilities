document.addEventListener("DOMContentLoaded", () => {
  const pickerButtons = document.querySelectorAll("[data-file-picker]");

  if (pickerButtons.length === 0) {
    return;
  }

  const browserUrl = "/file-browser/";
  const allowedTargets = {
    audios_dir: "audios",
    video_path: "video",
  };

  let browserWindow = null;

  function openBrowser(fieldName) {
    const target = allowedTargets[fieldName];

    if (!target) {
      return;
    }

    const params = new URLSearchParams({ target });
    const url = `${browserUrl}?${params.toString()}`;

    if (browserWindow && !browserWindow.closed) {
      browserWindow.close();
    }

    browserWindow = window.open(
      url,
      "videoMusicFileBrowser",
      "width=1100,height=800,resizable=yes,scrollbars=yes",
    );

    if (!browserWindow) {
      window.alert(
        "El navegador de archivos fue bloqueado. " +
          "Permite las ventanas emergentes para este sitio.",
      );
    }
  }

  pickerButtons.forEach((button) => {
    button.addEventListener("click", () => {
      openBrowser(button.dataset.filePicker);
    });
  });

  window.addEventListener("message", (event) => {
    if (event.origin !== window.location.origin) {
      return;
    }

    const data = event.data;

    if (
      !data ||
      data.type !== "file-browser-selection" ||
      !Object.hasOwn(allowedTargets, data.target) ||
      typeof data.path !== "string" ||
      !data.path
    ) {
      return;
    }

    const field = document.getElementById(`id_${data.target}`);

    if (!field) {
      return;
    }

    field.value = data.path;
    field.dispatchEvent(new Event("input", { bubbles: true }));
    field.dispatchEvent(new Event("change", { bubbles: true }));

    browserWindow = null;
    field.focus();
  });
});
