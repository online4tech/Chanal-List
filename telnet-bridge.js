#!/usr/bin/env node
/**
 * telnet-bridge.js — local WebSocket → Telnet bridge for the Control Center page.
 *
 * Setup (once):   npm install ws
 * Run:            node telnet-bridge.js
 *
 * Security:
 *  - Listens on 127.0.0.1 only (your own PC).
 *  - Only accepts pages from ALLOWED_ORIGINS (edit below or set env ALLOWED_ORIGINS="a,b").
 *  - Only connects to private LAN addresses (192.168.x.x / 10.x.x.x / 172.16-31.x.x).
 */
const { WebSocketServer } = require("ws");
const net = require("net");
const { StringDecoder } = require("string_decoder");

const PORT = Number(process.env.BRIDGE_PORT || 8765);
const ALLOWED_ORIGINS = (process.env.ALLOWED_ORIGINS ||
  "https://online4tech.github.io,http://localhost:5173,http://localhost:3000").split(",");
const PRIVATE = /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/;
const MARK = /__CC_DONE__(\d+)/;
const IDLE_MS = 5 * 60 * 1000;

const wss = new WebSocketServer({
  host: "127.0.0.1",
  port: PORT,
  verifyClient: ({ origin }) => ALLOWED_ORIGINS.includes(origin),
});
console.log(`Bridge listening on ws://127.0.0.1:${PORT}`);
console.log(`Allowed origins: ${ALLOWED_ORIGINS.join(", ")}`);

wss.on("connection", (ws) => {
  const send = (o) => ws.readyState === 1 && ws.send(JSON.stringify(o));

  ws.once("message", (raw) => {
    let req;
    try { req = JSON.parse(raw); } catch { return ws.close(); }
    const { host, port = 23, user = "root", password = "", command } = req;

    if (!PRIVATE.test(host || "") || typeof command !== "string" || !command.trim()) {
      send({ type: "error", message: "Invalid request (host must be a private LAN IP and command is required)" });
      return ws.close();
    }

    const sock = net.connect(Number(port), host);
    const decoder = new StringDecoder("utf8");
    let stage = "login"; // login → auth → run
    let buf = "";
    let finished = false;

    sock.setTimeout(IDLE_MS, () => { send({ type: "error", message: "Timed out" }); sock.destroy(); });
    sock.on("connect", () => send({ type: "data", data: `Connected to ${host}:${port}\n` }));
    sock.on("error", (e) => { send({ type: "error", message: e.message }); ws.close(); });
    sock.on("close", () => { if (!finished) send({ type: "error", message: "Connection closed" }); ws.close(); });
    ws.on("close", () => sock.destroy());

    sock.on("data", (chunk) => {
      // strip / answer telnet negotiation
      const out = [];
      for (let i = 0; i < chunk.length; i++) {
        if (chunk[i] !== 255) { out.push(chunk[i]); continue; }
        const cmd = chunk[i + 1];
        if (cmd === 250) { // subnegotiation: skip to IAC SE
          let j = i + 2;
          while (j < chunk.length && !(chunk[j] === 255 && chunk[j + 1] === 240)) j++;
          i = j + 1; continue;
        }
        if (cmd === 251 || cmd === 252) sock.write(Buffer.from([255, 254, chunk[i + 2]])); // WILL → DONT
        if (cmd === 253 || cmd === 254) sock.write(Buffer.from([255, 252, chunk[i + 2]])); // DO → WONT
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
          sock.write("exit\r\n");
          setTimeout(() => sock.end(), 300);
        } else if (buf.length > 200) buf = buf.slice(-200);
      }
    });
  });
});
