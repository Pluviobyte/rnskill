#!/usr/bin/env node
const fs = require("fs");
const http = require("http");
const path = require("path");
const { URL } = require("url");

function parseArgs(argv) {
  const args = {};
  for (let i = 2; i < argv.length; i += 1) {
    const key = argv[i];
    if (!key.startsWith("--")) continue;
    const name = key.slice(2);
    const next = argv[i + 1];
    if (!next || next.startsWith("--")) {
      args[name] = true;
    } else {
      args[name] = next;
      i += 1;
    }
  }
  return args;
}

function contentType(filePath) {
  const ext = path.extname(filePath).toLowerCase();
  return {
    ".html": "text/html; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".css": "text/css; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".mp4": "video/mp4",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".svg": "image/svg+xml",
    ".srt": "text/plain; charset=utf-8",
  }[ext] || "application/octet-stream";
}

function sendError(res, status, message) {
  res.writeHead(status, {
    "Content-Type": "text/plain; charset=utf-8",
    "Content-Length": Buffer.byteLength(message),
  });
  res.end(message);
}

function resolveFile(root, requestUrl) {
  const parsed = new URL(requestUrl, "http://127.0.0.1");
  const decoded = decodeURIComponent(parsed.pathname);
  const normalized = path.normalize(decoded).replace(/^(\.\.[/\\])+/, "");
  let filePath = path.join(root, normalized);
  if (!filePath.startsWith(root)) return null;
  if (fs.existsSync(filePath) && fs.statSync(filePath).isDirectory()) {
    filePath = path.join(filePath, "index.html");
  }
  return filePath;
}

function serveFile(req, res, filePath) {
  if (!filePath || !fs.existsSync(filePath) || !fs.statSync(filePath).isFile()) {
    sendError(res, 404, "File not found");
    return;
  }

  const stat = fs.statSync(filePath);
  const size = stat.size;
  const range = req.headers.range;
  const baseHeaders = {
    "Accept-Ranges": "bytes",
    "Content-Type": contentType(filePath),
    "Last-Modified": stat.mtime.toUTCString(),
  };

  if (range && range.startsWith("bytes=")) {
    const [startRaw, endRaw] = range.slice("bytes=".length).split("-");
    const start = startRaw ? Number(startRaw) : 0;
    const end = endRaw ? Math.min(Number(endRaw), size - 1) : size - 1;
    if (!Number.isFinite(start) || !Number.isFinite(end) || start > end || start >= size) {
      res.writeHead(416, {
        ...baseHeaders,
        "Content-Range": `bytes */${size}`,
      });
      res.end();
      return;
    }
    res.writeHead(206, {
      ...baseHeaders,
      "Content-Range": `bytes ${start}-${end}/${size}`,
      "Content-Length": String(end - start + 1),
    });
    if (req.method === "HEAD") {
      res.end();
      return;
    }
    fs.createReadStream(filePath, { start, end }).pipe(res);
    return;
  }

  res.writeHead(200, {
    ...baseHeaders,
    "Content-Length": String(size),
  });
  if (req.method === "HEAD") {
    res.end();
    return;
  }
  fs.createReadStream(filePath).pipe(res);
}

const args = parseArgs(process.argv);
const root = path.resolve(args["project-dir"] || ".");
const host = args.host || "127.0.0.1";
const port = Number(args.port || 8767);

if (!fs.existsSync(root) || !fs.statSync(root).isDirectory()) {
  console.error(`[error] project directory not found: ${root}`);
  process.exit(1);
}

const server = http.createServer((req, res) => {
  serveFile(req, res, resolveFile(root, req.url || "/"));
});

server.listen(port, host, () => {
  console.log(`[serve] http://${host}:${port}/`);
  console.log(`[open]  http://${host}:${port}/review/timeline-preview.html`);
});
