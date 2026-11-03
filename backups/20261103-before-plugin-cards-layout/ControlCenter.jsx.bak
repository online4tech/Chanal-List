/**
 * ControlCenter.jsx
 * Data-driven Control Center (React + TailwindCSS + lucide-react)
 *
 * Usage:
 *   import ControlCenter from "./ControlCenter";
 *   import data from "./data.json";           // { main: { panels: {...}, plugins: {...}, ... } }
 *   <ControlCenter data={data} onAction={(type, tool) => yourExistingApiCall(type, tool)} />
 *
 * - No hardcoded categories or tools: everything is derived from `data.main`.
 * - `onAction("install" | "update" | "remove", tool)` lets you plug in your EXISTING API.
 *   If omitted, the command is copied to the clipboard.
 * - Layout: 3 columns on desktop (lg+). Below lg it simply stacks (nothing desktop-specific leaks to mobile/tablet).
 */
import React, {
  memo, useCallback, useDeferredValue, useEffect, useMemo, useRef, useState,
} from "react";
import {
  Archive, ChevronRight, Copy, Download, FolderOpen, Home, Image as ImageIcon,
  LayoutPanelLeft, Loader, Film, Package, Palette, Power, Puzzle, RefreshCw,
  RotateCcw, Rss, Search, Terminal, Trash2, Tv, User, Wrench, X, Sparkles,
  Layers, Check,
} from "lucide-react";

/* ───────────────────────── 1. Icon mapping system ───────────────────────── */
// Add a line here to give any new section its own icon. Unknown keys fall back to Package.
const ICON_MAP = {
  panels: LayoutPanelLeft, plugins: Puzzle, channels: Tv, feeds: Rss, tools: Wrench,
  media: Film, skins: Palette, images: ImageIcon, picons: ImageIcon, bootlogos: Power,
  spinners: Loader, backup: Archive, restore: RotateCcw, default: Package,
};
const getIcon = (key) => ICON_MAP[String(key || "").toLowerCase().replace(/[\s_-]/g, "")] || ICON_MAP.default;

/* ───────────────────────── 2. JSON → normalized tree ───────────────────────── */
const TOOL_KEYS = ["install", "installCommand", "install_command", "command", "cmd", "url", "path",
  "remove", "removeCommand", "remove_command", "description", "desc", "status", "version"];
const CHILD_KEYS = ["subcategories", "children", "categories", "groups", "items", "tools"];
const META_KEYS = ["title", "name", "label", "icon", "description", "desc", "status"];

const isObj = (v) => v && typeof v === "object" && !Array.isArray(v);
const isTool = (v) =>
  typeof v === "string" ||
  (isObj(v) &&
    !CHILD_KEYS.some((k) => Array.isArray(v[k]) || isObj(v[k])) &&
    TOOL_KEYS.some((k) => typeof v[k] === "string" || typeof v[k] === "number"));

const prettify = (s) =>
  String(s).replace(/[_-]+/g, " ").replace(/([a-z])([A-Z])/g, "$1 $2").replace(/\b\w/g, (c) => c.toUpperCase());

const first = (o, keys) => { for (const k of keys) if (o[k] != null && o[k] !== "") return o[k]; return undefined; };

function toTool(raw, key, nodeId, idx) {
  const o = typeof raw === "string" ? { install: raw } : raw;
  const name = String(first(o, ["name", "title", "label"]) ?? key ?? `Tool ${idx + 1}`);
  return {
    id: `${nodeId}::${idx}::${name}`,
    nodeId,
    name,
    description: first(o, ["description", "desc"]) || "",
    install: first(o, ["install", "installCommand", "install_command", "command", "cmd", "url"]) || "",
    update: first(o, ["update", "updateCommand", "update_command"]) || "",
    remove: first(o, ["remove", "removeCommand", "remove_command", "uninstall"]) || "",
    path: o.path || "",
    status: o.status || o.version || "available",
    icon: o.icon,
  };
}

function buildNode(key, value, parent, root) {
  const id = parent ? `${parent.id}/${key}` : key;
  const node = {
    id, key, parent: parent?.id || null, root: root || id,
    label: prettify((isObj(value) && (value.title || value.name || value.label)) || key),
    icon: (isObj(value) && value.icon) || key,
    description: (isObj(value) && (value.description || value.desc)) || "",
    tools: [], children: [], count: 0,
  };
  const rootId = node.root;
  const addChild = (k, v) => node.children.push(buildNode(k, v, node, rootId));
  const addTool = (raw, k) => node.tools.push(toTool(raw, k, id, node.tools.length));

  const collectList = (arr) => arr.forEach((it, i) => {
    if (isTool(it)) addTool(it, undefined);
    else if (isObj(it)) addChild(it.name || it.title || `group-${i}`, it);
  });

  if (Array.isArray(value)) collectList(value);
  else if (isObj(value)) {
    for (const [k, v] of Object.entries(value)) {
      if (META_KEYS.includes(k) && typeof v === "string") continue;
      if (Array.isArray(v)) {
        if (k === "tools" || k === "items") collectList(v); else addChild(k, v);
      } else if (isObj(v)) {
        if (["subcategories", "children", "categories", "groups"].includes(k))
          Object.entries(v).forEach(([ck, cv]) => addChild(ck, cv));
        else if (isTool(v)) addTool(v, k);
        else addChild(k, v);
      } else if (typeof v === "string" && !TOOL_KEYS.includes(k)) addTool(v, k); // { "Tool name": "command" }
    }
  }
  node.count = node.tools.length + node.children.reduce((n, c) => n + c.count, 0);
  return node;
}

function buildModel(data) {
  const root = data?.main ?? data ?? {};
  const categories = Object.entries(root).map(([k, v]) => buildNode(k, v, null, null));
  const nodeById = new Map(), toolById = new Map(), index = [];
  const walk = (n) => {
    nodeById.set(n.id, n);
    index.push({ type: n.parent ? "sub" : "category", id: n.id, node: n, label: n.label, hay: n.label.toLowerCase() });
    n.tools.forEach((t) => {
      toolById.set(t.id, t);
      index.push({ type: "tool", id: t.id, tool: t, node: n, label: t.name,
        hay: `${t.name} ${t.description}`.toLowerCase() });
    });
    n.children.forEach(walk);
  };
  categories.forEach(walk);
  return { categories, nodeById, toolById, index };
}

/* ───────────────────────── 3. Shared styles ───────────────────────── */
const glass =
  "bg-white/5 backdrop-blur-[24px] border border-white/[0.08] shadow-[0_10px_40px_rgba(0,0,0,0.35)]";
const STATUS_STYLE = {
  installed: "bg-emerald-400/15 text-emerald-300 border-emerald-400/30",
  available: "bg-cyan-400/15 text-cyan-300 border-cyan-400/30",
  update: "bg-amber-400/15 text-amber-300 border-amber-400/30",
  default: "bg-violet-400/15 text-violet-300 border-violet-400/30",
};
const statusStyle = (s) => STATUS_STYLE[String(s).toLowerCase()] || STATUS_STYLE.default;

/* ───────────────────────── 4. Components ───────────────────────── */
const Header = memo(function Header({ query, setQuery, results, onPick, onHome }) {
  const [open, setOpen] = useState(false);
  const ref = useRef(null);
  useEffect(() => {
    const h = (e) => ref.current && !ref.current.contains(e.target) && setOpen(false);
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);
  return (
    <header className="relative z-30 border-b border-white/[0.06] bg-gradient-to-b from-white/[0.04] to-transparent">
      <div className="mx-auto grid max-w-[1700px] grid-cols-1 items-center gap-4 px-6 py-5 lg:grid-cols-[1fr_minmax(420px,640px)_1fr]">
        <button onClick={onHome} className="flex items-center gap-3 justify-self-start">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-gradient-to-br from-cyan-400 to-violet-600 shadow-[0_0_30px_rgba(139,92,246,0.55)]">
            <Sparkles className="h-5 w-5 text-white" />
          </span>
          <span className="text-left leading-tight">
            <span className="block text-lg font-semibold tracking-wide text-white">Control Center</span>
            <span className="block text-xs text-slate-400">Manage everything in one place</span>
          </span>
        </button>

        <div ref={ref} className="relative">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            value={query}
            onChange={(e) => { setQuery(e.target.value); setOpen(true); }}
            onFocus={() => setOpen(true)}
            placeholder="Search categories, sub categories and tools…"
            className="h-12 w-full rounded-2xl border border-white/10 bg-white/[0.06] pl-11 pr-10 text-sm text-white placeholder-slate-500 outline-none backdrop-blur-xl transition focus:border-cyan-400/50 focus:shadow-[0_0_0_4px_rgba(34,211,238,0.12)]"
          />
          {query && (
            <button onClick={() => setQuery("")} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white">
              <X className="h-4 w-4" />
            </button>
          )}
          {open && query.trim() && (
            <div className={`${glass} absolute left-0 right-0 top-14 max-h-[420px] overflow-y-auto rounded-2xl bg-slate-900/80 p-2`}>
              {results.length === 0 && <p className="p-4 text-sm text-slate-400">No results</p>}
              {results.map((r) => {
                const Icon = r.type === "tool" ? getIcon(r.tool.icon || r.node.root) : getIcon(r.node.icon);
                return (
                  <button key={r.id} onClick={() => { onPick(r); setOpen(false); }}
                    className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition hover:bg-white/10">
                    <Icon className="h-4 w-4 shrink-0 text-cyan-300" />
                    <span className="min-w-0 flex-1">
                      <span className="block truncate text-sm text-white">{r.label}</span>
                      {r.type !== "category" && (
                        <span className="block truncate text-xs text-slate-500">{r.node.label}</span>
                      )}
                    </span>
                    <span className="rounded-md bg-white/10 px-2 py-0.5 text-[10px] uppercase tracking-wider text-slate-300">
                      {r.type === "sub" ? "sub category" : r.type}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        <div className="flex items-center gap-3 justify-self-end">
          <div className="hidden text-right sm:block leading-tight">
            <span className="block text-sm text-white">Administrator</span>
            <span className="block text-xs text-slate-400">Online</span>
          </div>
          <span className="grid h-11 w-11 place-items-center rounded-full border border-white/10 bg-white/10">
            <User className="h-5 w-5 text-slate-200" />
          </span>
        </div>
      </div>
    </header>
  );
});

const Breadcrumbs = memo(function Breadcrumbs({ items }) {
  return (
    <nav className="mb-5 flex flex-wrap items-center gap-1.5 text-sm">
      {items.map((it, i) => {
        const last = i === items.length - 1;
        return (
          <React.Fragment key={`${it.label}-${i}`}>
            {i > 0 && <ChevronRight className="h-3.5 w-3.5 text-slate-600" />}
            <button disabled={last} onClick={it.onClick}
              className={`flex items-center gap-1.5 rounded-lg px-2 py-1 transition ${
                last ? "text-white" : "text-slate-400 hover:bg-white/10 hover:text-white"}`}>
              {i === 0 && <Home className="h-3.5 w-3.5" />}
              {it.label}
            </button>
          </React.Fragment>
        );
      })}
    </nav>
  );
});

const CategoryCard = memo(function CategoryCard({ node, active, onSelect }) {
  const Icon = getIcon(node.icon);
  return (
    <button onClick={() => onSelect(node.id)}
      className={`group relative flex w-full items-center gap-3 overflow-hidden rounded-2xl border p-3.5 text-left transition-all duration-300 ${
        active
          ? "border-cyan-400/40 bg-gradient-to-r from-cyan-400/15 to-violet-500/15 shadow-[0_0_30px_rgba(34,211,238,0.18)]"
          : "border-white/[0.08] bg-white/5 hover:border-white/20 hover:bg-white/[0.09] hover:shadow-[0_0_28px_rgba(139,92,246,0.22)]"}`}>
      {active && <span className="absolute left-0 top-1/4 h-1/2 w-1 rounded-r-full bg-cyan-300" />}
      <span className={`grid h-10 w-10 shrink-0 place-items-center rounded-xl transition ${
        active ? "bg-cyan-400/20 text-cyan-200" : "bg-white/10 text-slate-300 group-hover:text-white"}`}>
        <Icon className="h-5 w-5" />
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-sm font-medium text-white">{node.label}</span>
        <span className="block text-xs text-slate-500">{node.count} items</span>
      </span>
    </button>
  );
});

const ToolCard = memo(function ToolCard({ tool, rootKey, selected, onSelect, stacked }) {
  const Icon = getIcon(tool.icon || rootKey);
  return (
    <button onClick={() => onSelect(tool.id)}
      className={`group flex flex-col gap-3 rounded-2xl border p-4 text-left transition-all duration-300 hover:-translate-y-1 ${stacked ? "h-[132px]" : ""} ${
        selected
          ? "border-cyan-400/50 bg-cyan-400/10 shadow-[0_0_34px_rgba(34,211,238,0.25)]"
          : "border-white/[0.08] bg-white/5 hover:border-violet-400/40 hover:bg-white/[0.09] hover:shadow-[0_12px_40px_rgba(139,92,246,0.28)]"}`}>
      <div className="flex items-start justify-between gap-2">
        <span className="grid h-11 w-11 place-items-center rounded-xl bg-gradient-to-br from-cyan-400/20 to-violet-500/20 text-cyan-200">
          <Icon className="h-5 w-5" />
        </span>
        <span className={`rounded-full border px-2.5 py-0.5 text-[11px] capitalize ${statusStyle(tool.status)}`}>
          {tool.status}
        </span>
      </div>
      <div className="min-w-0">
        <h3 className="truncate text-sm font-semibold text-white">{tool.name}</h3>
        <p className="mt-1 line-clamp-2 min-h-[2.5rem] text-xs leading-relaxed text-slate-400">
          {tool.description || tool.path || "No description"}
        </p>
      </div>
    </button>
  );
});

const SubCategoryCard = memo(function SubCategoryCard({ node, onSelect }) {
  const Icon = node.key === "Media" ? getIcon(node.icon) : node.children.length ? Layers : FolderOpen;
  return (
    <button onClick={() => onSelect(node.id)}
      className="group flex h-14 items-center gap-3 rounded-2xl border border-white/[0.08] bg-white/5 p-3.5 text-left transition-all hover:-translate-y-0.5 hover:border-cyan-400/40 hover:bg-white/[0.09] hover:shadow-[0_0_28px_rgba(34,211,238,0.18)]">
      <Icon className="h-5 w-5 text-violet-300" />
      <span className="min-w-0 flex-1 truncate text-sm text-white">{node.label}</span>
      <span className="rounded-md bg-white/10 px-2 py-0.5 text-xs text-slate-300">{node.count}</span>
    </button>
  );
});

const PAGE = 60;
const ToolGrid = memo(function ToolGrid({ node, selectedToolId, onSelectTool, onSelectNode }) {
  const [limit, setLimit] = useState(PAGE); // reset by `key` on the parent when node changes
  const shown = node.tools.slice(0, limit);
  const stacked = node.root === "plugins";
  return (
    <div className="space-y-6">
      {node.children.length > 0 && (
        <section>
          <h2 className="mb-3 text-xs font-medium uppercase tracking-widest text-slate-500">Sub categories</h2>
          <div className={`grid grid-cols-1 gap-3 ${stacked ? "" : "sm:grid-cols-2 xl:grid-cols-3"}`}>
            {node.children.map((c) => <SubCategoryCard key={c.id} node={c} onSelect={onSelectNode} />)}
          </div>
        </section>
      )}
      {node.tools.length > 0 && (
        <section>
          <h2 className="mb-3 text-xs font-medium uppercase tracking-widest text-slate-500">
            Tools · {node.tools.length}
          </h2>
          <div className={`grid grid-cols-1 gap-4 ${stacked ? "" : "sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4"}`}>
            {shown.map((t) => (
              <ToolCard key={t.id} tool={t} rootKey={node.key === "Media" ? "media" : node.root} selected={t.id === selectedToolId} onSelect={onSelectTool} stacked={stacked} />
            ))}
          </div>
          {limit < node.tools.length && (
            <button onClick={() => setLimit((l) => l + PAGE)}
              className="mx-auto mt-6 block rounded-xl border border-white/10 bg-white/10 px-5 py-2 text-sm text-white transition hover:bg-white/20">
              Show more ({node.tools.length - limit})
            </button>
          )}
        </section>
      )}
      {node.tools.length === 0 && node.children.length === 0 && (
        <p className="py-16 text-center text-sm text-slate-500">Nothing here yet.</p>
      )}
    </div>
  );
});

const CopyRow = ({ icon: Icon, label, value }) => {
  const [done, setDone] = useState(false);
  if (!value) return null;
  const copy = () => navigator.clipboard?.writeText(String(value)).then(() => { setDone(true); setTimeout(() => setDone(false), 1200); });
  return (
    <div>
      <div className="mb-1.5 flex items-center justify-between text-xs text-slate-400">
        <span className="flex items-center gap-1.5"><Icon className="h-3.5 w-3.5" />{label}</span>
        <button onClick={copy} className="text-slate-500 transition hover:text-white">
          {done ? <Check className="h-3.5 w-3.5 text-emerald-300" /> : <Copy className="h-3.5 w-3.5" />}
        </button>
      </div>
      <code className="block max-h-28 overflow-auto break-all rounded-xl border border-white/[0.08] bg-black/30 p-3 text-xs text-cyan-100">
        {value}
      </code>
    </div>
  );
};

const DetailsPanel = memo(function DetailsPanel({ tool, rootKey, onAction }) {
  if (!tool)
    return (
      <aside className={`${glass} sticky top-6 grid min-h-[320px] place-items-center rounded-3xl p-8 text-center`}>
        <div>
          <Sparkles className="mx-auto mb-3 h-8 w-8 text-violet-300/60" />
          <p className="text-sm text-slate-400">Select a tool to see its details</p>
        </div>
      </aside>
    );
  const Icon = getIcon(tool.icon || rootKey);
  const btn = "flex items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-40";
  return (
    <aside className={`${glass} sticky top-6 space-y-5 rounded-3xl p-6`}>
      <div className="flex items-start gap-4">
        <span className="grid h-14 w-14 shrink-0 place-items-center rounded-2xl bg-gradient-to-br from-cyan-400/25 to-violet-500/25 text-cyan-200">
          <Icon className="h-7 w-7" />
        </span>
        <div className="min-w-0">
          <h2 className="break-words text-lg font-semibold text-white">{tool.name}</h2>
          <span className={`mt-1 inline-block rounded-full border px-2.5 py-0.5 text-[11px] capitalize ${statusStyle(tool.status)}`}>
            {tool.status}
          </span>
        </div>
      </div>
      {tool.description && <p className="text-sm leading-relaxed text-slate-300">{tool.description}</p>}
      <CopyRow icon={Terminal} label="Install command" value={tool.install} />
      <CopyRow icon={FolderOpen} label="Path" value={tool.path} />
      <CopyRow icon={Trash2} label="Remove command" value={tool.remove} />
      <div className="grid grid-cols-3 gap-2 pt-1">
        <button disabled={!tool.install} onClick={() => onAction("install", tool)}
          className={`${btn} bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-[0_0_24px_rgba(34,211,238,0.3)] hover:brightness-110`}>
          <Download className="h-4 w-4" />Install
        </button>
        <button disabled={!tool.update && !tool.install} onClick={() => onAction("update", tool)}
          className={`${btn} border border-white/10 bg-white/10 text-white hover:bg-white/20`}>
          <RefreshCw className="h-4 w-4" />Update
        </button>
        <button disabled={!tool.remove} onClick={() => onAction("remove", tool)}
          className={`${btn} border border-rose-400/30 bg-rose-500/15 text-rose-200 hover:bg-rose-500/25`}>
          <Trash2 className="h-4 w-4" />Remove
        </button>
      </div>
    </aside>
  );
});

/* ───────────────────────── 5. Page ───────────────────────── */
/* ───────────────────────── Telnet runner (talks to telnet-bridge.js) ───────────────────────── */
const BRIDGE_URL = "ws://127.0.0.1:8765";
const ANSI = /\x1b\[[0-9;?]*[A-Za-z]/g;

function TelnetRunner({ job, onClose }) {
  const [cfg, setCfg] = useState(() => {
    const base = { host: "", port: 23, user: "root", pass: "" };
    try { return { ...base, ...JSON.parse(localStorage.getItem("cc-receiver") || "{}") }; } catch { return base; }
  });
  const [log, setLog] = useState("");
  const [state, setState] = useState("idle"); // idle | running | done | error
  const [code, setCode] = useState(null);
  const wsRef = useRef(null);
  const boxRef = useRef(null);

  useEffect(() => () => wsRef.current?.close(), []);
  useEffect(() => { if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight; }, [log]);

  const set = (k) => (e) => setCfg((c) => ({ ...c, [k]: e.target.value }));

  const run = () => {
    try { localStorage.setItem("cc-receiver", JSON.stringify({ host: cfg.host, port: cfg.port, user: cfg.user })); } catch {}
    setLog(""); setCode(null); setState("running");
    let ws;
    try { ws = new WebSocket(BRIDGE_URL); } catch { setState("error"); setLog("Cannot open the local bridge.\n"); return; }
    wsRef.current = ws;
    ws.onopen = () => ws.send(JSON.stringify({
      host: cfg.host.trim(), port: Number(cfg.port) || 23, user: cfg.user, password: cfg.pass, command: job.command,
    }));
    ws.onmessage = (e) => {
      let m; try { m = JSON.parse(e.data); } catch { return; }
      if (m.type === "data") setLog((l) => (l + m.data.replace(ANSI, "")).slice(-20000));
      if (m.type === "done") { setCode(m.code); setState("done"); }
      if (m.type === "error") { setLog((l) => `${l}\n[error] ${m.message}\n`); setState("error"); }
    };
    ws.onerror = () => {
      setState("error");
      setLog("Cannot reach the local bridge.\nRun it first:  node telnet-bridge.js\n");
    };
    ws.onclose = () => setState((s) => (s === "running" ? "error" : s));
  };

  const input = "h-10 w-full rounded-xl border border-white/10 bg-white/[0.06] px-3 text-sm text-white outline-none focus:border-cyan-400/50";
  const running = state === "running";
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-black/60 p-4 backdrop-blur-sm">
      <div className={`${glass} w-full max-w-2xl space-y-4 rounded-3xl bg-slate-900/80 p-6`}>
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
            <Terminal className="h-5 w-5 text-cyan-300" />
            {job.type[0].toUpperCase() + job.type.slice(1)} · {job.tool.name}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white"><X className="h-5 w-5" /></button>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <input className={input} placeholder="Receiver IP" value={cfg.host} onChange={set("host")} disabled={running} />
          <input className={input} placeholder="Port" value={cfg.port} onChange={set("port")} disabled={running} />
          <input className={input} placeholder="User" value={cfg.user} onChange={set("user")} disabled={running} />
          <input className={input} placeholder="Password" type="password" value={cfg.pass} onChange={set("pass")} disabled={running} />
        </div>

        <code className="block max-h-24 overflow-auto break-all rounded-xl border border-white/[0.08] bg-black/30 p-3 text-xs text-cyan-100">
          {job.command}
        </code>

        <pre ref={boxRef}
          className="h-64 overflow-auto whitespace-pre-wrap break-words rounded-xl border border-white/[0.08] bg-black/50 p-3 text-xs leading-relaxed text-emerald-200">
          {log || "Output will appear here…"}
        </pre>

        <div className="flex items-center justify-between">
          <span className={`text-sm ${state === "done" && code === 0 ? "text-emerald-300" : state === "error" || (state === "done" && code !== 0) ? "text-rose-300" : "text-slate-400"}`}>
            {state === "idle" && "Ready"}
            {running && "Running…"}
            {state === "done" && (code === 0 ? "Finished successfully" : `Finished with exit code ${code}`)}
            {state === "error" && "Failed"}
          </span>
          <div className="flex gap-2">
            <button onClick={onClose} className="rounded-xl border border-white/10 bg-white/10 px-4 py-2 text-sm text-white hover:bg-white/20">Close</button>
            <button onClick={run} disabled={running || !cfg.host.trim()}
              className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-5 py-2 text-sm font-medium text-white disabled:opacity-40">
              <Download className="h-4 w-4" />{running ? "Running…" : "Run on receiver"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ControlCenter({ data, onAction }) {
  const model = useMemo(() => buildModel(data), [data]);
  const { categories, nodeById, toolById, index } = model;

  const [selectedCategory, setSelectedCategory] = useState(null);
  const [selectedSubCategory, setSelectedSubCategory] = useState(null);
  const [selectedTool, setSelectedTool] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [toast, setToast] = useState("");
  const [job, setJob] = useState(null); // { type, tool, command } → opens the Telnet runner
  const deferredQuery = useDeferredValue(searchQuery);

  // default to the first category once data is available
  useEffect(() => {
    if (!selectedCategory && categories[0]) setSelectedCategory(categories[0].id);
  }, [categories, selectedCategory]);

  const results = useMemo(() => {
    const q = deferredQuery.trim().toLowerCase();
    if (!q) return [];
    const out = [];
    for (const e of index) { if (e.hay.includes(q)) { out.push(e); if (out.length >= 40) break; } }
    return out;
  }, [deferredQuery, index]);

  const goHome = useCallback(() => {
    setSelectedCategory(categories[0]?.id ?? null); setSelectedSubCategory(null); setSelectedTool(null); setSearchQuery("");
  }, [categories]);
  const pickCategory = useCallback((id) => { setSelectedCategory(id); setSelectedSubCategory(null); setSelectedTool(null); }, []);
  const pickNode = useCallback((id) => {
    const n = nodeById.get(id); if (!n) return;
    setSelectedCategory(n.root); setSelectedSubCategory(n.parent ? id : null); setSelectedTool(null);
  }, [nodeById]);
  const pickTool = useCallback((id) => {
    const t = toolById.get(id); if (!t) return;
    const n = nodeById.get(t.nodeId);
    setSelectedCategory(n.root); setSelectedSubCategory(n.parent ? n.id : null); setSelectedTool(id);
  }, [toolById, nodeById]);
  const pickSearch = useCallback((r) => {
    if (r.type === "tool") pickTool(r.id); else pickNode(r.id);
    setSearchQuery("");
  }, [pickTool, pickNode]);

  const activeNode = nodeById.get(selectedSubCategory || selectedCategory) || null;
  const activeTool = selectedTool ? toolById.get(selectedTool) : null;

  const crumbs = useMemo(() => {
    const list = [{ label: "Home", onClick: goHome }];
    if (!activeNode) return list;
    const chain = []; let n = activeNode;
    while (n) { chain.unshift(n); n = n.parent ? nodeById.get(n.parent) : null; }
    chain.forEach((c) => list.push({ label: c.label, onClick: () => (c.parent ? pickNode(c.id) : pickCategory(c.id)) }));
    if (activeTool) list.push({ label: activeTool.name, onClick: () => {} });
    return list;
  }, [activeNode, activeTool, nodeById, goHome, pickNode, pickCategory]);

  const handleAction = useCallback((type, tool) => {
    if (onAction) return onAction(type, tool);
    const cmd = type === "install" ? tool.install : type === "update" ? tool.update || tool.install : tool.remove;
    if (!cmd) return;
    setJob({ type, tool, command: cmd });
  }, [onAction]);

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#070a1a] text-slate-200">
      {/* ambient background */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,#14183f_0%,#070a1a_60%)]" />
        <div className="absolute -left-40 top-20 h-[520px] w-[520px] rounded-full bg-violet-600/25 blur-[140px]" />
        <div className="absolute right-[-120px] top-[-80px] h-[460px] w-[460px] rounded-full bg-cyan-500/20 blur-[140px]" />
        <div className="absolute bottom-[-160px] left-1/3 h-[420px] w-[620px] rounded-full bg-blue-700/20 blur-[150px]" />
      </div>

      <div className="relative">
        <Header query={searchQuery} setQuery={setSearchQuery} results={results} onPick={pickSearch} onHome={goHome} />

        <main className="mx-auto grid max-w-[1700px] grid-cols-1 gap-6 px-6 py-6 lg:grid-cols-[260px_minmax(0,1fr)_360px]">
          {/* Left rail */}
          <section className="lg:sticky lg:top-6 lg:max-h-[calc(100vh-3rem)] lg:self-start lg:overflow-y-auto">
            <div className="space-y-2.5 lg:pr-1">
              {categories.map((c) => (
                <CategoryCard key={c.id} node={c} active={c.id === selectedCategory} onSelect={pickCategory} />
              ))}
            </div>
          </section>

          {/* Content */}
          <section className="min-w-0">
            <Breadcrumbs items={crumbs} />
            {activeNode && (
              <>
                <div className="mb-6">
                  <h1 className="text-2xl font-semibold text-white">{activeNode.label}</h1>
                  <p className="mt-1 text-sm text-slate-400">
                    {activeNode.description || `${activeNode.count} items`}
                  </p>
                </div>
                <ToolGrid
                  key={activeNode.id}
                  node={activeNode}
                  selectedToolId={selectedTool}
                  onSelectTool={pickTool}
                  onSelectNode={pickNode}
                />
              </>
            )}
          </section>

          {/* Details */}
          <section className="min-w-0">
            <DetailsPanel tool={activeTool} rootKey={activeNode?.key === "Media" ? "media" : activeNode?.root} onAction={handleAction} />
          </section>
        </main>
      </div>

      {job && <TelnetRunner job={job} onClose={() => setJob(null)} />}
      {toast && (
        <div className={`${glass} fixed bottom-6 left-1/2 z-50 -translate-x-1/2 rounded-xl bg-slate-900/80 px-4 py-2 text-sm text-white`}>
          {toast}
        </div>
      )}
    </div>
  );
}
