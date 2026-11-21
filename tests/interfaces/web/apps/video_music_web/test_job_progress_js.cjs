const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const scriptPath = path.resolve(
  __dirname,
  "../../../../../interfaces/web/static/video_music_web/js/job_progress.js",
);
const script = fs.readFileSync(scriptPath, "utf8");

function createClock() {
  let currentTime = 0;
  let nextId = 1;
  const tasks = new Map();

  return {
    setTimeout(callback, delay) {
      const id = nextId++;
      tasks.set(id, { callback, runAt: currentTime + delay });
      return id;
    },
    clearTimeout(id) {
      tasks.delete(id);
    },
    async advance(milliseconds) {
      const targetTime = currentTime + milliseconds;

      while (true) {
        const nextTask = [...tasks.entries()]
          .filter(([, task]) => task.runAt <= targetTime)
          .sort((left, right) => left[1].runAt - right[1].runAt)[0];

        if (!nextTask) {
          break;
        }

        const [id, task] = nextTask;
        tasks.delete(id);
        currentTime = task.runAt;
        task.callback();
        await flushPromises();
      }

      currentTime = targetTime;
      await flushPromises();
    },
  };
}

async function flushPromises() {
  for (let index = 0; index < 8; index += 1) {
    await Promise.resolve();
  }
}

function createResponse(status = "running", tracks = []) {
  return {
    ok: true,
    async json() {
      return {
        job: {
          job_id: "job-123",
          status,
          message: "Estado del trabajo",
          current_directory: 1,
          total_directories: 1,
          completed_tracks: 0,
          total_tracks: 0,
          running_tracks: 0,
          failed_tracks: 0,
          tracks,
        },
      };
    },
  };
}

class FakeNode {
  constructor(tagName, textContent = "") {
    this.tagName = tagName;
    this.children = [];
    this.className = "";
    this.id = "";
    this._textContent = textContent;
  }

  get textContent() {
    return (
      this._textContent +
      this.children.map((child) => child.textContent).join("")
    );
  }

  set textContent(value) {
    this._textContent = String(value);
    this.children = [];
  }

  append(...nodes) {
    this.children.push(...nodes);
  }

  replaceChildren(...nodes) {
    this.children = nodes;
  }

  after() {}

  replaceWith() {}
}

function createHarness(fetchImplementation) {
  const clock = createClock();
  const elements = new Map();
  const createdNodes = [];

  for (const id of [
    "job-status",
    "job-message",
    "job-error",
    "current-directory",
    "total-directories",
    "completed-tracks",
    "total-tracks",
    "running-tracks",
    "failed-tracks",
    "track-list",
    "no-tracks",
  ]) {
    elements.set(id, { textContent: "", after() {} });
  }
  elements.set("track-list", null);
  elements.set("no-tracks", null);

  const config = {
    dataset: {
      statusUrl: "/jobs/job-123/status/",
      resultUrl: "/video-music/jobs/job-123/results/",
    },
  };
  const location = {
    origin: "http://localhost",
    assignedUrl: null,
    assign(url) {
      this.assignedUrl = url;
    },
  };
  const window = {
    setTimeout: clock.setTimeout,
    clearTimeout: clock.clearTimeout,
    location,
  };
  const document = {
    getElementById(id) {
      return id === "job-progress-config" ? config : elements.get(id) ?? null;
    },
    createElement(tagName) {
      const node = new FakeNode(tagName);
      createdNodes.push(node);
      return node;
    },
    createTextNode(text) {
      return new FakeNode("#text", text);
    },
    createDocumentFragment() {
      return new FakeNode("#fragment");
    },
  };

  vm.runInNewContext(script, {
    AbortController,
    URL,
    console: { error() {} },
    document,
    fetch: fetchImplementation,
    window,
  });

  return { clock, elements, location, createdNodes };
}

test("does not start another request while the current request is pending", async () => {
  let requestCount = 0;
  let activeRequests = 0;
  let maxActiveRequests = 0;
  let resolveRequest;

  const harness = createHarness(() => {
    requestCount += 1;
    activeRequests += 1;
    maxActiveRequests = Math.max(maxActiveRequests, activeRequests);

    return new Promise((resolve) => {
      resolveRequest = () => {
        activeRequests -= 1;
        resolve(createResponse());
      };
    });
  });

  await harness.clock.advance(9000);
  assert.equal(requestCount, 1);

  resolveRequest();
  await flushPromises();
  await harness.clock.advance(1000);

  assert.equal(requestCount, 2);
  assert.equal(maxActiveRequests, 1);
});

test("renders Spanish colored states and moves completed tracks last", async () => {
  const tracks = [
    { name: "completada", status: "completed", message: "Completada" },
    { name: "pendiente", status: "pending", message: "Pendiente" },
    { name: "fallida", status: "failed", message: "Fallida" },
    {
      name: "activa",
      status: "running",
      message: "Duración detectada: 00:01:17.200",
      duration: "00:01:17.200",
    },
  ];
  const harness = createHarness(() =>
    Promise.resolve(createResponse("running", tracks)),
  );

  await flushPromises();

  const list = harness.createdNodes.find((node) => node.tagName === "ul");
  const renderedTracks = list.children[0].children;

  assert.deepEqual(
    renderedTracks.map((item) => item.children[0].textContent),
    [
      "⏳ Pendiente | pendiente",
      "❌ Fallida | fallida",
      "🔄 En procesamiento | activa | 00:01:17.200",
      "✅ Completada | completada",
    ],
  );
  assert.deepEqual(
    renderedTracks.map((item) => item.children[0].className),
    ["flex flex-wrap items-center gap-2 text-sm font-semibold text-gray-400",
      "flex flex-wrap items-center gap-2 text-sm font-semibold text-red-300",
      "flex flex-wrap items-center gap-2 text-sm font-semibold text-blue-300",
      "flex flex-wrap items-center gap-2 text-sm font-semibold text-green-300"],
  );
  assert.ok(
    renderedTracks.every(
      (item) => !/pending|running|completed|failed/.test(item.textContent),
    ),
  );
  assert.equal(renderedTracks[2].children.length, 1);
});

test("aborts a timed out request and retries with an increased delay", async () => {
  let requestCount = 0;
  let abortCount = 0;

  const harness = createHarness((_url, options) => {
    requestCount += 1;

    if (requestCount > 1) {
      return new Promise(() => {});
    }

    return new Promise((_resolve, reject) => {
      options.signal.addEventListener("abort", () => {
        abortCount += 1;
        const error = new Error("Request aborted");
        error.name = "AbortError";
        reject(error);
      });
    });
  });

  await harness.clock.advance(10000);
  assert.equal(abortCount, 1);
  assert.match(
    harness.elements.get("job-message").textContent,
    /tardó demasiado/,
  );

  await harness.clock.advance(1999);
  assert.equal(requestCount, 1);
  await harness.clock.advance(1);
  assert.equal(requestCount, 2);
});

test("backs off after failures and resets the delay after success", async () => {
  let requestCount = 0;
  const harness = createHarness(() => {
    requestCount += 1;

    if (requestCount <= 2) {
      return Promise.reject(new Error("Temporary failure"));
    }

    return requestCount === 3
      ? Promise.resolve(createResponse())
      : new Promise(() => {});
  });

  await flushPromises();
  assert.equal(requestCount, 1);

  await harness.clock.advance(1999);
  assert.equal(requestCount, 1);
  await harness.clock.advance(1);
  assert.equal(requestCount, 2);

  await harness.clock.advance(3999);
  assert.equal(requestCount, 2);
  await harness.clock.advance(1);
  assert.equal(requestCount, 3);

  await harness.clock.advance(999);
  assert.equal(requestCount, 3);
  await harness.clock.advance(1);
  assert.equal(requestCount, 4);
});

test("caps the retry delay at fifteen seconds", async () => {
  let requestCount = 0;
  const harness = createHarness(() => {
    requestCount += 1;
    return Promise.reject(new Error("Temporary failure"));
  });

  await flushPromises();
  assert.equal(requestCount, 1);

  let expectedRequestCount = 1;
  for (const retryDelay of [2000, 4000, 8000, 15000, 15000]) {
    await harness.clock.advance(retryDelay - 1);
    assert.equal(requestCount, expectedRequestCount);
    await harness.clock.advance(1);
    expectedRequestCount += 1;
    assert.equal(requestCount, expectedRequestCount);
  }
});

test("stops polling after the job reaches a terminal status", async () => {
  let requestCount = 0;
  const harness = createHarness(() => {
    requestCount += 1;
    return Promise.resolve(createResponse("failed"));
  });

  await flushPromises();
  assert.equal(requestCount, 1);
  assert.equal(
    harness.location.assignedUrl,
    "/video-music/jobs/job-123/results/",
  );

  await harness.clock.advance(60000);
  assert.equal(requestCount, 1);
});
