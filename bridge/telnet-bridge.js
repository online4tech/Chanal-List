#!/usr/bin/env node
/**
 * Online4Tech Bridge — local WebSocket -> Telnet bridge for the Control Center page.
 *
 * Needs only Node.js (https://nodejs.org). No "npm install" and no extra packages.
 * Run:  node telnet-bridge.js        (or double-click start-bridge.bat on Windows)
 *
 * Security:
 *  - Listens on 127.0.0.1 only (your own computer).
 *  - Accepts only pages from ALLOWED_ORIGINS (env ALLOWED_ORIGINS="a,b" to change).
 *  - Only connects to private LAN addresses (192.168.x.x / 10.x.x.x / 172.16-31.x.x).
 */
const http = require("http");
const net = require("net");
const crypto = require("crypto");
const { StringDecoder } = require("string_decoder");

const PORT = Number(process.env.BRIDGE_PORT || 8765);
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS ||
  "https://online4tech.github.io,http://localhost:5173,http://localhost:3000").split(",").map((s) => s.trim());
const PRIVATE = process.env.BRIDGE_TEST_ALLOW_LOOPBACK === "1"
  ? /^(127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/
  : /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/;
const MARK = /__CC_DONE__(\d+)/;
const IDLE_MS = 5 * 60 * 1000;
const MAX_MSG = 1024 * 1024;
const GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";

/* ───────────── minimal WebSocket server (RFC 6455, text frames) ───────────── */
function frame(opcode, payload) {
  const len = payload.length;
  let head;
  if (len < 126) head = Buffer.from([0x80 | opcode, len]);
  else if (len < 65536) { head = Buffer.alloc(4); head[0] = 0x80 | opcode; head[1] = 126; head.writeUInt16BE(len, 2); }
  else { head = Buffer.alloc(10); head[0] = 0x80 | opcode; head[1] = 127; head.writeBigUInt64BE(BigInt(len), 2); }
  return Buffer.concat([head, payload]);
}

function wrapSocket(socket) {
  let buf = Buffer.alloc(0);
  let parts = [];
  let partOp = 0;
  const ws = {
    closed: false,
    onmessage: null,
    onclose: null,
    send(text) { if (!ws.closed) socket.write(frame(0x1, Buffer.from(text, "utf8"))); },
    close() {
      if (ws.closed) return;
      ws.closed = true;
      try { socket.write(frame(0x8, Buffer.alloc(0))); socket.end(); } catch { /* ignore */ }
    },
  };

  const handle = (fin, op, payload) => {
    if (op === 0x8) return ws.close();
    if (op === 0x9) return void socket.write(frame(0xa, payload));
    if (op === 0xa) return;
    if (op === 0x1 || op === 0x2) { parts = [payload]; partOp = op; }
    else if (op === 0x0) parts.push(payload);
    else return;
    if (fin) {
      const msg = Buffer.concat(parts);
      parts = [];
      if (partOp === 0x1 && ws.onmessage) ws.onmessage(msg.toString("utf8"));
    }
  };

  const parse = () => {
    while (buf.length >= 2) {
      const fin = !!(buf[0] & 0x80);
      const op = buf[0] & 0x0f;
      const masked = !!(buf[1] & 0x80);
      let len = buf[1] & 0x7f;
      let off = 2;
      if (len === 126) { if (buf.length < 4) return; len = buf.readUInt16BE(2); off = 4; }
      else if (len === 127) {
        if (buf.length < 10) return;
        const big = buf.readBigUInt64BE(2);
        if (big > BigInt(MAX_MSG)) return ws.close();
        len = Number(big); off = 10;
      }
      if (len > MAX_MSG || !masked) return ws.close(); // browsers always mask
      if (buf.length < off + 4 + len) return;
      const mask = buf.subarray(off, off + 4);
      const payload = Buffer.from(buf.subarray(off + 4, off + 4 + len));
      for (let i = 0; i < payload.length; i++) payload[i] ^= mask[i & 3];
      buf = buf.subarray(off + 4 + len);
      handle(fin, op, payload);
    }
  };

  socket.on("data", (chunk) => { buf = Buffer.concat([buf, chunk]); parse(); });
  socket.on("close", () => { ws.closed = true; if (ws.onclose) ws.onclose(); });
  socket.on("error", () => socket.destroy());
  return ws;
}

const server = http.createServer((req, res) => {
  res.writeHead(200, { "Content-Type": "text/plain; charset=utf-8" });
  res.end("Online4Tech Bridge is running.\n");
});

server.on("upgrade", (req, socket) => {
  const reject = (code, text) => { socket.write(`HTTP/1.1 ${code} ${text}\r\nConnection: close\r\n\r\n`); socket.destroy(); };
  const host = String(req.headers.host || "").toLowerCase();
  if (host !== `127.0.0.1:${PORT}` && host !== `localhost:${PORT}`) return reject(403, "Forbidden"); // DNS-rebinding guard
  if (!ALLOWED_ORIGINS.includes(req.headers.origin)) return reject(403, "Forbidden");
  const key = req.headers["sec-websocket-key"];
  if (!key || String(req.headers.upgrade).toLowerCase() !== "websocket") return reject(400, "Bad Request");
  const accept = crypto.createHash("sha1").update(key + GUID).digest("base64");
  socket.write(
    "HTTP/1.1 101 Switching Protocols\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n" +
    `Sec-WebSocket-Accept: ${accept}\r\n\r\n`
  );
  session(wrapSocket(socket));
});

/* ───────────── one Telnet session per WebSocket connection ───────────── */
function session(ws) {
  const send = (o) => ws.send(JSON.stringify(o));
  let started = false;

  ws.onmessage = (raw) => {
    if (started) return; // one request per connection
    started = true;
    let req;
    try { req = JSON.parse(raw); } catch { return ws.close(); }
    const { host, port = 23, user = "root", password = "", command } = req;

    if (!PRIVATE.test(host || "") || typeof command !== "string" || !command.trim()) {
      send({ type: "error", message: "Invalid request (host must be a private LAN IP and command is required)" });
      return ws.close();
    }

    const sock = net.connect(Number(port), host);
    const decoder = new StringDecoder("utf8");
    let stage = "login"; // login -> auth -> run
    let buf = "";
    let finished = false;

    sock.setTimeout(IDLE_MS, () => { send({ type: "error", message: "Timed out" }); sock.destroy(); });
    sock.on("connect", () => send({ type: "data", data: `Connected to ${host}:${port}\n` }));
    sock.on("error", (e) => { if (!finished) send({ type: "error", message: e.message }); ws.close(); });
    sock.on("close", () => { if (!finished) send({ type: "error", message: "Connection closed" }); ws.close(); });
    ws.onclose = () => sock.destroy();

    sock.on("data", (chunk) => {
      if (finished) return; // command already reported as done: ignore the receiver's goodbye (exit echo, prompts)
      // strip and answer Telnet negotiation
      const out = [];
      for (let i = 0; i < chunk.length; i++) {
        if (chunk[i] !== 255) { out.push(chunk[i]); continue; }
        const cmd = chunk[i + 1];
        if (cmd === 250) { // subnegotiation: skip to IAC SE
          let j = i + 2;
          while (j < chunk.length && !(chunk[j] === 255 && chunk[j + 1] === 240)) j++;
          i = j + 1; continue;
        }
        if (cmd === 251 || cmd === 252) sock.write(Buffer.from([255, 254, chunk[i + 2]])); // WILL -> DONT
        if (cmd === 253 || cmd === 254) sock.write(Buffer.from([255, 252, chunk[i + 2]])); // DO -> WONT
        i += cmd >= 251 && cmd <= 254 ? 2 : 1;
      }
      const text = decoder.write(Buffer.from(out)).replace(/\r/g, "");
      if (!text) return;
      buf += text;

      if (stage === "login") {
        if (/login:\s*$/i.test(buf)) { sock.write(user + "\r\n"); stage = "auth"; buf = ""; }
        else if (/[#$]\s*$/.test(buf)) { stage = "auth"; } // already at a shell
        else return;
      }
      if (stage === "auth") {
        if (/assword:\s*$/i.test(buf)) { sock.write(password + "\r\n"); buf = ""; return; }
        if (/incorrect|denied|failed/i.test(buf)) {
          send({ type: "error", message: "Login failed" }); finished = true; return sock.end();
        }
        if (/[#$]\s*$/.test(buf)) {
          stage = "run"; buf = "";
          sock.write(`${command}; echo __CC_DO''NE__$?\r\n`);
        }
        return;
      }
      if (stage === "run") {
        const m = buf.match(MARK);
        send({ type: "data", data: text.replace(/__CC_DONE__\d*/g, "") });
        if (m) {
          finished = true;
          send({ type: "done", code: Number(m[1]) });
          try { sock.write("exit\r\n"); } catch { /* connection already closing */ }
          setTimeout(() => sock.destroy(), 300);
        } else if (buf.length > 200) buf = buf.slice(-200);
      }
    });
  };
}

server.on("error", (e) => {
  if (e.code === "EADDRINUSE") {
    console.log(`\nPort ${PORT} is already in use. The bridge is probably already running (maybe hidden).`);
    console.log("Nothing else to do: you can use the Control Center page now.");
  } else console.log("Bridge error:", e.message);
  process.exit(1);
});

server.listen(PORT, "127.0.0.1", () => {
  console.log("==========================================");
  console.log(" Online4Tech Bridge is running");
  console.log(` Address: ws://127.0.0.1:${PORT}`);
  console.log(" Keep this window open while you use the page.");
  console.log("==========================================");
});
