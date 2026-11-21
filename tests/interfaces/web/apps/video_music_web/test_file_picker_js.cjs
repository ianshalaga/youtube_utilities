const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const scriptPath = path.resolve(
  __dirname,
  "../../../../../interfaces/web/static/video_music_web/js/file_picker.js",
);
const script = fs.readFileSync(scriptPath, "utf8");

test("moves the file browser below the field that opened it", () => {
  const handlers = new Map();
  const buttons = [
    {
      dataset: { filePicker: "audios_dir" },
      addEventListener: (name, callback) =>
        handlers.set("audios_dir", callback),
    },
    {
      dataset: { filePicker: "video_path" },
      addEventListener: (name, callback) =>
        handlers.set("video_path", callback),
    },
  ];
  const placements = [];
  const containers = {
    audios_dir: {
      insertAdjacentElement(position, panel) {
        placements.push(["audios_dir", position, panel]);
      },
    },
    video_path: {
      insertAdjacentElement(position, panel) {
        placements.push(["video_path", position, panel]);
      },
    },
  };
  const browserPanel = {
    dataset: {},
    hidden: true,
    classList: { remove() {}, add() {} },
    scrollIntoView() {},
  };
  const closeButton = {
    addEventListener(name, callback) {
      handlers.set("close", callback);
    },
  };
  const description = { textContent: "" };
  let onReady;
  const document = {
    addEventListener(name, callback) {
      onReady = callback;
    },
    querySelectorAll() {
      return buttons;
    },
    querySelector(selector) {
      const fieldName = selector.match(
        /\[data-file-picker-container="(.+)"\]/,
      )?.[1];
      return containers[fieldName] || null;
    },
    getElementById(id) {
      return {
        "file-browser-panel": browserPanel,
        "file-browser-close": closeButton,
        "file-browser-description": description,
      }[id] || null;
    },
  };
  const dispatchedEvents = [];
  const window = {
    addEventListener() {},
    dispatchEvent(event) {
      dispatchedEvents.push(event);
    },
  };

  vm.runInNewContext(script, {
    document,
    window,
    CustomEvent: class {
      constructor(type, options) {
        this.type = type;
        this.detail = options.detail;
      }
    },
  });
  onReady();
  handlers.get("audios_dir")();

  assert.deepEqual(placements[0], ["audios_dir", "afterend", browserPanel]);
  assert.equal(browserPanel.hidden, false);
  assert.equal(browserPanel.dataset.target, "audios");
  assert.equal(dispatchedEvents[0].detail.target, "audios");

  handlers.get("video_path")();

  assert.deepEqual(placements[1], ["video_path", "afterend", browserPanel]);
  assert.equal(browserPanel.dataset.target, "video");
});
