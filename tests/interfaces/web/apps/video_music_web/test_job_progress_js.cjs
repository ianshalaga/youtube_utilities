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

function createResponse(status = "running") {
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
          tracks: [],
        },
      };
    },
  };
}

function createHarness(fetchImplementation) {
  const clock = createClock();
  const elements = new Map();

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

  const config = { dataset: { statusUrl: "/jobs/job-123/status/" } };
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
  };

  vm.runInNewContext(script, {
    AbortController,
    URL,
    console: { error() {} },
    document,
    fetch: fetchImplementation,
    window,
  });

  return { clock, elements, location };
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
    "http://localhost/video-music/?job_id=job-123",
  );

  await harness.clock.advance(60000);
  assert.equal(requestCount, 1);
});
