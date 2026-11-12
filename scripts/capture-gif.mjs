#!/usr/bin/env node
/**
 * Capture an animated GIF of a local HTML page using headless Chrome + the
 * Chrome DevTools Protocol.
 *
 *   node scripts/capture-gif.mjs <file.html> <out.gif> [durationMs] [fps]
 *
 * Chrome is driven over a raw CDP WebSocket (Node's global WebSocket), so the
 * script needs no npm dependencies. Frames are grabbed with Page.captureScreenshot
 * and stitched together with ffmpeg.
 */
import { spawn, execFileSync } from "node:child_process";
import { mkdtemp, rm, writeFile, mkdir } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, dirname, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const CHROME_CANDIDATES = [
  process.env.CHROME_PATH,
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/Applications/Chromium.app/Contents/MacOS/Chromium",
  "google-chrome",
  "chromium",
  "chromium-browser",
].filter(Boolean);

const [, , pageArg, outArg, durArg = "2400", fpsArg = "20"] = process.argv;
if (!pageArg || !outArg) {
  console.error("usage: node scripts/capture-gif.mjs <file.html> <out.gif> [durationMs] [fps]");
  process.exit(2);
}

const durationMs = Number(durArg);
const fps = Number(fpsArg);
const width = Number(process.env.GIF_WIDTH || 560);
const height = Number(process.env.GIF_HEIGHT || 320);
const pageUrl = pathToFileURL(resolve(pageArg)).href;

function findChrome() {
  for (const c of CHROME_CANDIDATES) {
    try {
      if (c.startsWith("/")) {
        execFileSync("test", ["-x", c]);
      } else {
        execFileSync("which", [c]);
      }
      return c;
    } catch {
      /* try the next candidate */
    }
  }
  throw new Error("no Chrome/Chromium binary found; set CHROME_PATH");
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function waitForDevTools(port, timeoutMs = 15000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    try {
      const res = await fetch(`http://127.0.0.1:${port}/json/version`);
      if (res.ok) return await res.json();
    } catch {
      /* not up yet */
    }
    await sleep(150);
  }
  throw new Error("timed out waiting for Chrome DevTools endpoint");
}

const chrome = findChrome();
const profile = await mkdtemp(join(tmpdir(), "fl-gif-"));
const port = 9222 + Math.floor(Math.random() * 900);

const proc = spawn(
  chrome,
  [
    "--headless=new",
    "--disable-gpu",
    "--hide-scrollbars",
    "--mute-audio",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-extensions",
    "--force-device-scale-factor=2",
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profile}`,
    `--window-size=${width},${height}`,
    "about:blank",
  ],
  { stdio: "ignore" },
);

const cleanup = async () => {
  try { proc.kill("SIGKILL"); } catch { /* already gone */ }
  await rm(profile, { recursive: true, force: true }).catch(() => {});
};

try {
  await waitForDevTools(port);
  const targets = await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();
  const target = targets.find((t) => t.type === "page");
  if (!target) throw new Error("no page target");

  const ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise((res, rej) => {
    ws.addEventListener("open", res, { once: true });
    ws.addEventListener("error", rej, { once: true });
  });

  let nextId = 1;
  const pending = new Map();
  ws.addEventListener("message", (event) => {
    const msg = JSON.parse(event.data);
    if (msg.id && pending.has(msg.id)) {
      const { resolve, reject } = pending.get(msg.id);
      pending.delete(msg.id);
      if (msg.error) reject(new Error(msg.error.message));
      else resolve(msg.result);
    }
  });

  const send = (method, params = {}) =>
    new Promise((resolve, reject) => {
      const id = nextId++;
      pending.set(id, { resolve, reject });
      ws.send(JSON.stringify({ id, method, params }));
    });

  await send("Page.enable");
  await send("Runtime.enable");
  await send("Emulation.setDeviceMetricsOverride", {
    width,
    height,
    deviceScaleFactor: 2,
    mobile: false,
  });

  await send("Page.navigate", { url: pageUrl });
  // Give the page time to load fonts/layout before the first frame.
  await sleep(900);

  const frames = [];
  const total = Math.max(2, Math.round((durationMs / 1000) * fps));
  const interval = 1000 / fps;
  const start = Date.now();

  for (let i = 0; i < total; i++) {
    const target_time = start + i * interval;
    const wait = target_time - Date.now();
    if (wait > 0) await sleep(wait);
    const { data } = await send("Page.captureScreenshot", { format: "png", captureBeyondViewport: false });
    frames.push(Buffer.from(data, "base64"));
  }

  ws.close();

  const outPath = resolve(outArg);
  await mkdir(dirname(outPath), { recursive: true });
  const frameDir = await mkdtemp(join(tmpdir(), "fl-frames-"));
  for (let i = 0; i < frames.length; i++) {
    const name = join(frameDir, `f${String(i).padStart(4, "0")}.png`);
    await writeFile(name, frames[i]);
  }

  const palette = join(frameDir, "palette.png");
  execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-i", `${frameDir}/f%04d.png`, "-vf", "palettegen=stats_mode=diff", palette]);
  execFileSync("ffmpeg", [
    "-y", "-loglevel", "error", "-i", `${frameDir}/f%04d.png`, "-i", palette,
    "-lavfi", "paletteuse=dither=bayer:bayer_scale=3", "-loop", "0", outPath,
  ]);

  await rm(frameDir, { recursive: true, force: true });
  console.log(`wrote ${outPath} (${frames.length} frames)`);
} catch (err) {
  console.error("capture failed:", err.message);
  process.exitCode = 1;
} finally {
  await cleanup();
}
