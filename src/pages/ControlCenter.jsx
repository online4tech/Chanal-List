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
  Layers, Check, Monitor, Smartphone, ExternalLink, Wifi, WifiOff,
  MonitorPlay, SlidersHorizontal, KeyRound, Languages, Shapes, Images, Cpu,
} from "lucide-react";

/* ───────────────────────── 1. Theme: icon + accent color per section ───────────────────────── */
// Add a line here to give a section its own icon and color (a = "R G B").
// Unknown keys fall back to a stable color picked from their name, so new data never looks broken.
const THEMES = {
  panels: { a: "167 139 250", icon: LayoutPanelLeft, intro: "لوحات متكاملة تجمع عشرات الأدوات والإضافات والخدمات في واجهة واحدة على الرسيفر." },
  plugins: { a: "34 211 238", icon: Puzzle, intro: "إضافات Enigma2 لتشغيل IPTV والوسائط والسوفتكام والترجمة وضبط الإعدادات، وتُثبَّت بأمر واحد." },
  channels: { a: "96 165 250", icon: Tv, intro: "قوائم قنوات جاهزة ومحدّثة للأقمار المختلفة، تُثبَّت مباشرة على الرسيفر." },
  feeds: { a: "251 146 60", icon: Rss, intro: "مصادر حزم (Feeds) تضيفها للرسيفر لتثبيت وتحديث الإضافات من مستودعاتها." },
  tools: { a: "251 191 36", icon: Wrench, intro: "أدوات مساعدة لصيانة الرسيفر وإدارة النظام والملفات." },
  media: { a: "255 107 0", icon: Film, intro: "مشغّلات وإضافات للوسائط والأفلام والمسلسلات على الرسيفر." },
  skins: { a: "232 121 249", icon: Palette, intro: "واجهات (Skins) تغيّر شكل الرسيفر وقوائمه وتمنحه مظهرًا جديدًا." },
  images: { a: "129 140 248", icon: ImageIcon, intro: "صور نظام (Images) كاملة للرسيفر مع روابط التحميل والتثبيت." },
  picons: { a: "52 211 153", icon: Images, intro: "أيقونات القنوات (Picons) التي تظهر بجانب اسم كل قناة في القائمة." },
  bootlogos: { a: "248 113 113", icon: Power, intro: "شعارات الإقلاع (Bootlogos) التي تظهر عند تشغيل الرسيفر." },
  spinners: { a: "45 212 191", icon: Loader, intro: "أيقونات التحميل المتحركة (Spinners) التي تظهر أثناء انتظار فتح الشاشات." },
  backup: { a: "74 222 128", icon: Archive, intro: "أدوات النسخ الاحتياطي لقوائم القنوات والإعدادات والصور." },
  restore: { a: "56 189 248", icon: RotateCcw, intro: "استرجاع النسخ الاحتياطية والإعدادات والقوائم السابقة إلى الرسيفر." },
  // plugin sub categories
  iptv: { a: "0 200 255", icon: MonitorPlay, intro: "إضافات تشغيل IPTV وقوائم Xtream وM3U على الرسيفر." },
  settings: { a: "77 154 255", icon: SlidersHorizontal, intro: "إضافات لضبط إعدادات الرسيفر والنظام." },
  softcam: { a: "139 92 246", icon: KeyRound, intro: "إضافات وأدوات SoftCam لإدارة الكامات على الرسيفر." },
  translation: { a: "46 204 113", icon: Languages, intro: "إضافات الترجمة والترجمات (Subtitles) وتعريب الواجهة." },
  other: { a: "148 163 184", icon: Shapes, intro: "إضافات متنوعة لا تندرج تحت تصنيف محدد." },
};
const ACCENT_POOL = ["34 211 238", "167 139 250", "96 165 250", "251 146 60", "251 191 36", "52 211 153", "232 121 249", "45 212 191"];
const normKey = (k) => String(k || "").toLowerCase().replace(/[\s_-]/g, "");
const ICON_MAP = { ...Object.fromEntries(Object.entries(THEMES).map(([k, v]) => [k, v.icon])), default: Package };
const getIcon = (key) => ICON_MAP[normKey(key)] || ICON_MAP.default;

function themeFor(node) {
  if (!node) return { a: "34 211 238", Icon: Package };
  for (const k of [node.key, node.root]) {
    const t = THEMES[normKey(k)];
    if (t) return { a: t.a, Icon: t.icon };
  }
  const h = [...String(node.root || node.key)].reduce((n, c) => (n * 31 + c.charCodeAt(0)) >>> 0, 7);
  return { a: ACCENT_POOL[h % ACCENT_POOL.length], Icon: getIcon(node.icon) };
}

// Descriptions look like "text | المطور: Name | صور مذكور توافقها: OpenATV" — split them into text + chips.
function parseDesc(desc) {
  const parts = String(desc || "").split("|").map((s) => s.trim()).filter(Boolean);
  const out = { text: parts[0] || "", dev: "", compat: "" };
  for (const p of parts.slice(1)) {
    const i = p.indexOf(":");
    if (i < 0) continue;
    const k = p.slice(0, i), v = p.slice(i + 1).trim();
    if (!v) continue;
    if (/المطور|developer|author/i.test(k)) out.dev = v;
    else if (/توافق|compat|image/i.test(k)) out.compat = v;
  }
  return out;
}

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
      <div className="grid w-full grid-cols-1 items-center gap-4 px-6 py-5 lg:grid-cols-[1fr_minmax(420px,640px)_1fr]">
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

const StatusPill = ({ status }) => (
  <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[11px] font-medium capitalize ${statusStyle(status)}`}>
    <span className="h-1.5 w-1.5 rounded-full bg-current" />{status}
  </span>
);

const Chip = ({ icon: Icon, children, className = "" }) => (
  <span className={`inline-flex min-w-0 items-center gap-1.5 rounded-lg bg-white/[0.06] px-2 py-1 text-[11px] text-slate-300 ${className}`}>
    <Icon className="cc-accent h-3 w-3 shrink-0" /><span className="truncate" dir="auto">{children}</span>
  </span>
);

const CategoryCard = memo(function CategoryCard({ node, active, onSelect }) {
  const theme = themeFor(node);
  const Icon = theme.Icon;
  return (
    <button onClick={() => onSelect(node.id)} style={{ "--a": theme.a }}
      className={`cc-nav group ${active ? "is-active" : ""}`}>
      <span className="cc-tile cc-tile-sm"><Icon className="h-5 w-5" /></span>
      <span className="min-w-0 flex-1 text-start">
        <span className="block truncate text-sm font-medium text-white">{node.label}</span>
        <span className="block text-xs text-slate-500">{node.count} items</span>
      </span>
      <ChevronRight className="cc-nav-arrow h-4 w-4 shrink-0" />
    </button>
  );
});

const ToolCard = memo(function ToolCard({ tool, theme, selected, onSelect }) {
  const Icon = tool.icon ? getIcon(tool.icon) : theme.Icon;
  const d = useMemo(() => parseDesc(tool.description), [tool.description]);
  return (
    <button onClick={() => onSelect(tool.id)} style={{ "--a": theme.a }}
      className={`cc-card group ${selected ? "is-selected" : ""}`}>
      <div className="flex items-start justify-between gap-3">
        <span className="cc-tile"><Icon className="h-6 w-6" /></span>
        <StatusPill status={tool.status} />
      </div>
      <div className="min-w-0">
        <h3 className="truncate text-[15px] font-semibold text-white">{tool.name}</h3>
        <p dir="auto" className="mt-1.5 line-clamp-2 text-start text-[13px] leading-relaxed text-slate-400">
          {d.text || "No description"}
        </p>
      </div>
      <div className="mt-auto flex min-h-[26px] items-center gap-1.5">
        {d.dev && <Chip icon={User}>{d.dev}</Chip>}
        {d.compat && <Chip icon={Cpu} className="max-w-[48%] shrink-0">{d.compat}</Chip>}
      </div>
    </button>
  );
});

const SubCategoryCard = memo(function SubCategoryCard({ node, onSelect }) {
  const theme = themeFor(node);
  const Icon = theme.Icon;
  return (
    <button onClick={() => onSelect(node.id)} style={{ "--a": theme.a }} className="cc-sub group">
      <span className="cc-tile cc-tile-sm"><Icon className="h-5 w-5" /></span>
      <span className="min-w-0 flex-1 truncate text-start text-[15px] font-semibold text-white">{node.label}</span>
      <span className="cc-count">{node.count}</span>
      <ChevronRight className="cc-nav-arrow h-4 w-4 shrink-0" />
    </button>
  );
});

const PAGE = 60;
const ToolGrid = memo(function ToolGrid({ node, theme, selectedToolId, onSelectTool, onSelectNode }) {
  const [limit, setLimit] = useState(PAGE); // reset by `key` on the parent when node changes
  const shown = node.tools.slice(0, limit);
  return (
    <div className="space-y-8">
      {node.children.length > 0 && (
        <section>
          <h2 className="cc-eyebrow mb-3">Sub categories</h2>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-3 min-[1900px]:grid-cols-4">
            {node.children.map((c) => <SubCategoryCard key={c.id} node={c} onSelect={onSelectNode} />)}
          </div>
        </section>
      )}
      {node.tools.length > 0 && (
        <section>
          <h2 className="cc-eyebrow mb-3">Tools · {node.tools.length}</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 min-[1900px]:grid-cols-5 min-[2400px]:grid-cols-6">
            {shown.map((t) => (
              <ToolCard key={t.id} tool={t} theme={theme} selected={t.id === selectedToolId} onSelect={onSelectTool} />
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

const DetailsPanel = memo(function DetailsPanel({ tool, theme, node, onAction, onCopy }) {
  if (!tool) {
    const HeadIcon = theme.Icon;
    const intro = (node && (THEMES[normKey(node.key)]?.intro || node.description || THEMES[normKey(node.root)]?.intro)) || "";
    const subs = node?.children?.length || 0;
    return (
      <aside style={{ "--a": theme.a }} className="cc-panel flex flex-col items-center gap-5 px-6 py-9 text-center">
        <div className="cc-emblem" aria-hidden="true">
          <span className="cc-emblem-ring" /><span className="cc-emblem-ring cc-emblem-ring-2" />
          <span className="cc-emblem-core"><HeadIcon className="h-11 w-11" /></span>
        </div>
        <div className="min-w-0">
          <p className="cc-eyebrow mb-1.5">القسم</p>
          <h2 className="break-words text-xl font-semibold tracking-tight text-white">{node?.label || "Control Center"}</h2>
        </div>
        {intro && <p dir="auto" className="max-w-[300px] text-sm leading-7 text-slate-300">{intro}</p>}
        {node && (
          <div className={`grid w-full gap-2.5 ${subs ? "grid-cols-2" : "grid-cols-1"}`}>
            <div className="cc-stat"><b>{node.count}</b><span>أداة</span></div>
            {subs > 0 && <div className="cc-stat"><b>{subs}</b><span>تصنيف فرعي</span></div>}
          </div>
        )}
      </aside>
    );
  }
  const Icon = tool.icon ? getIcon(tool.icon) : theme.Icon;
  const d = parseDesc(tool.description);
  const btn = "flex items-center justify-center gap-2 rounded-xl px-3 py-2.5 text-sm font-medium transition disabled:cursor-not-allowed disabled:opacity-40";
  return (
    <aside style={{ "--a": theme.a }} className="cc-panel space-y-5 p-6">
      <div className="flex items-start gap-4">
        <span className="cc-tile cc-tile-lg"><Icon className="h-7 w-7" /></span>
        <div className="min-w-0 pt-0.5">
          <h2 className="break-words text-lg font-semibold leading-snug text-white">{tool.name}</h2>
          <div className="mt-1.5"><StatusPill status={tool.status} /></div>
        </div>
      </div>
      {d.text && <p dir="auto" className="text-start text-sm leading-7 text-slate-300">{d.text}</p>}
      {(d.dev || d.compat) && (
        <div className="flex flex-wrap gap-2">
          {d.dev && <Chip icon={User}>{d.dev}</Chip>}
          {d.compat && <Chip icon={Cpu}>{d.compat}</Chip>}
        </div>
      )}
      <div className="grid grid-cols-3 gap-2 pt-1">
        <button disabled={!tool.install} onClick={() => onAction("install", tool)}
          className={`${btn} bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-[0_0_24px_rgba(34,211,238,0.3)] hover:brightness-110`}>
          <Download className="h-4 w-4" />Install
        </button>
        <button disabled={!tool.install} onClick={() => onCopy(tool)}
          className={`${btn} border border-white/10 bg-white/10 text-white hover:bg-white/20`}>
          <Copy className="h-4 w-4" />Copy
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
/* ───────────────────────── Telnet runner (talks to the local bridge, or manual mode) ───────────────────────── */
const BRIDGE_URL = "ws://127.0.0.1:8765";
const BRIDGE_ZIP = "../bridge/Online4Tech-Bridge.zip"; // served next to /control-center/ on GitHub Pages
const ANSI = /\x1b\[[0-9;?]*[A-Za-z]/g;
const IS_MOBILE = typeof navigator !== "undefined" && /Android|iPhone|iPad|iPod/i.test(navigator.userAgent || "");
const TERMIUS_PLAY = "https://play.google.com/store/apps/details?id=com.server.auditor.ssh.client";
const TERMIUS_IOS = "https://apps.apple.com/app/termius-terminal-ssh-client/id549039908";
const PUTTY_URL = "https://www.putty.org";

// Checks (without sending anything) whether the local bridge answers on this computer.
function useBridgeStatus() {
  const [status, setStatus] = useState("checking"); // checking | online | offline
  const check = useCallback(() => {
    setStatus("checking");
    let settled = false, ws, timer;
    const finish = (s) => {
      if (settled) return;
      settled = true; clearTimeout(timer); setStatus(s);
      try { ws && ws.close(); } catch { /* ignore */ }
    };
    try { ws = new WebSocket(BRIDGE_URL); } catch { finish("offline"); return; }
    timer = setTimeout(() => finish("offline"), 2500);
    ws.onopen = () => finish("online");
    ws.onerror = () => finish("offline");
  }, []);
  useEffect(() => { check(); }, [check]);
  return [status, check];
}

function CopyButton({ text, label = "نسخ", className = "" }) {
  const [done, setDone] = useState(false);
  const copy = async () => {
    try { await navigator.clipboard.writeText(String(text)); setDone(true); setTimeout(() => setDone(false), 1500); } catch { /* ignore */ }
  };
  return (
    <button type="button" onClick={copy}
      className={`flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/10 px-4 py-2 text-sm text-white transition hover:bg-white/20 ${className}`}>
      {done ? <Check className="h-4 w-4 text-emerald-300" /> : <Copy className="h-4 w-4" />}
      {done ? "تم النسخ" : label}
    </button>
  );
}

function TelnetRunner({ job, onClose }) {
  const [cfg, setCfg] = useState(() => {
    const base = { host: "", port: 23, user: "root", pass: "" };
    try { return { ...base, ...JSON.parse(localStorage.getItem("cc-receiver") || "{}") }; } catch { return base; }
  });
  const [log, setLog] = useState("");
  const [state, setState] = useState("idle"); // idle | running | done | error
  const [code, setCode] = useState(null);
  const [bridge, recheck] = useBridgeStatus();
  const [picked, setPicked] = useState(IS_MOBILE ? "manual" : null); // null = choose automatically
  const wsRef = useRef(null);
  const boxRef = useRef(null);

  const mode = picked || (bridge === "offline" ? "manual" : "bridge");

  useEffect(() => () => wsRef.current?.close(), []);
  useEffect(() => { if (boxRef.current) boxRef.current.scrollTop = boxRef.current.scrollHeight; }, [log]);

  const set = (k) => (e) => setCfg((c) => ({ ...c, [k]: e.target.value }));
  const remember = () => {
    try { localStorage.setItem("cc-receiver", JSON.stringify({ host: cfg.host, port: cfg.port, user: cfg.user })); } catch { /* ignore */ }
  };

  const run = () => {
    remember();
    setLog(""); setCode(null); setState("running");
    let ws;
    try { ws = new WebSocket(BRIDGE_URL); } catch { setState("error"); setLog("Cannot open the local bridge.\n"); return; }
    wsRef.current = ws;
    let finished = false; // once "done" arrives, later messages (goodbye noise from old bridges) are ignored
    ws.onopen = () => ws.send(JSON.stringify({
      host: cfg.host.trim(), port: Number(cfg.port) || 23, user: cfg.user, password: cfg.pass, command: job.command,
    }));
    ws.onmessage = (e) => {
      if (finished) return;
      let m; try { m = JSON.parse(e.data); } catch { return; }
      if (m.type === "data") setLog((l) => (l + m.data.replace(ANSI, "")).slice(-20000));
      if (m.type === "done") { finished = true; setCode(m.code); setState("done"); }
      if (m.type === "error") { finished = true; setLog((l) => `${l}\n[error] ${m.message}\n`); setState("error"); }
    };
    ws.onerror = () => {
      if (finished) return;
      setState("error");
      setLog("الجسر غير شغال على الكمبيوتر ده.\nافتح ملف start-bridge.bat ثم جرّب تاني.\n");
      recheck();
    };
    ws.onclose = () => setState((s) => (s === "running" ? "error" : s));
  };

  const input = "h-10 w-full rounded-xl border border-white/10 bg-white/[0.06] px-3 text-sm text-white outline-none focus:border-cyan-400/50";
  const running = state === "running";
  const host = cfg.host.trim();
  const tab = (id, label, Icon) => (
    <button type="button" onClick={() => setPicked(id)}
      className={`flex flex-1 items-center justify-center gap-2 rounded-xl px-3 py-2 text-sm transition ${
        mode === id ? "bg-gradient-to-r from-cyan-500/30 to-violet-500/30 text-white ring-1 ring-cyan-400/40" : "text-slate-400 hover:bg-white/10 hover:text-white"}`}>
      <Icon className="h-4 w-4" />{label}
    </button>
  );
  const badge = {
    checking: ["text-slate-300 border-white/10 bg-white/5", "جاري فحص الجسر…"],
    online: ["text-emerald-300 border-emerald-400/30 bg-emerald-400/10", "الجسر شغال على الكمبيوتر ده"],
    offline: ["text-amber-300 border-amber-400/30 bg-amber-400/10", "الجسر غير شغال"],
  }[bridge];

  return (
    <div className="fixed inset-0 z-50 grid place-items-center overflow-y-auto bg-black/60 p-4 backdrop-blur-sm">
      <div className={`${glass} my-auto w-full max-w-2xl space-y-4 rounded-3xl bg-slate-900/90 p-6`}>
        <div className="flex items-center justify-between">
          <h3 className="flex items-center gap-2 text-lg font-semibold text-white">
            <Terminal className="h-5 w-5 text-cyan-300" />
            {job.type[0].toUpperCase() + job.type.slice(1)} · {job.tool.name}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white"><X className="h-5 w-5" /></button>
        </div>

        <div className="flex gap-2 rounded-2xl border border-white/10 bg-black/20 p-1.5">
          {tab("bridge", "تنفيذ مباشر (كمبيوتر)", Monitor)}
          {tab("manual", "يدوي (موبايل أو أي جهاز)", Smartphone)}
        </div>

        <input className={input} placeholder="Receiver IP  مثال: 192.168.1.50" value={cfg.host}
          onChange={set("host")} disabled={running} inputMode="decimal" dir="ltr" />

        <code dir="ltr" className="block max-h-24 overflow-auto break-all rounded-xl border border-white/[0.08] bg-black/30 p-3 text-xs text-cyan-100">
          {job.command}
        </code>

        {mode === "bridge" ? (
          <>
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs ${badge[0]}`}>
                {bridge === "offline" ? <WifiOff className="h-3.5 w-3.5" /> : <Wifi className="h-3.5 w-3.5" />}{badge[1]}
              </span>
              <button type="button" onClick={recheck} className="text-xs text-slate-400 underline hover:text-white">إعادة الفحص</button>
            </div>

            {bridge === "offline" && (
              <div dir="rtl" className="space-y-2 rounded-xl border border-amber-400/25 bg-amber-400/10 p-3 text-sm leading-7 text-amber-100">
                <p>التنفيذ المباشر محتاج برنامج الجسر الصغير على الكمبيوتر (مرة واحدة):</p>
                <ol className="list-decimal space-y-1 pr-5">
                  <li><a className="underline" href={BRIDGE_ZIP} download>حمّل ملف الجسر</a> وفك الضغط في فولدر تحتفظ به.</li>
                  <li>اضغط دبل كليك على <b dir="ltr">start-bridge.bat</b> واترك النافذة مفتوحة.</li>
                  <li>ارجع هنا واضغط "إعادة الفحص".</li>
                </ol>
                <p className="text-xs opacity-80">من الموبايل أو لو مش عايز تحمّل حاجة، استخدم تبويب "يدوي".</p>
              </div>
            )}

            <div className="grid grid-cols-3 gap-3">
              <input className={input} placeholder="Port" value={cfg.port} onChange={set("port")} disabled={running} dir="ltr" />
              <input className={input} placeholder="User" value={cfg.user} onChange={set("user")} disabled={running} dir="ltr" />
              <input className={input} placeholder="Password" type="password" value={cfg.pass} onChange={set("pass")} disabled={running} dir="ltr" />
            </div>

            <pre ref={boxRef} dir="ltr"
              className="h-56 overflow-auto whitespace-pre-wrap break-words rounded-xl border border-white/[0.08] bg-black/50 p-3 text-xs leading-relaxed text-emerald-200">
              {log || "Output will appear here…"}
            </pre>

            <div className="flex items-center justify-between">
              <span className={`text-sm ${state === "done" && code === 0 ? "text-emerald-300" : state === "error" || (state === "done" && code !== 0) ? "text-rose-300" : "text-slate-400"}`}>
                {state === "idle" && "جاهز"}
                {running && "جاري التنفيذ…"}
                {state === "done" && (code === 0 ? "تم التنفيذ بنجاح" : `انتهى بكود خطأ ${code}`)}
                {state === "error" && "فشل"}
              </span>
              <div className="flex gap-2">
                <button onClick={onClose} className="rounded-xl border border-white/10 bg-white/10 px-4 py-2 text-sm text-white hover:bg-white/20">إغلاق</button>
                <button onClick={run} disabled={running || !host}
                  className="flex items-center gap-2 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-5 py-2 text-sm font-medium text-white disabled:opacity-40">
                  <Download className="h-4 w-4" />{running ? "جاري التنفيذ…" : "نفّذ على الرسيفر"}
                </button>
              </div>
            </div>
          </>
        ) : (
          <div dir="rtl" className="space-y-4">
            <ol className="list-decimal space-y-3 pr-5 text-sm leading-7 text-slate-200">
              <li>
                ثبّت تطبيق اتصال بالرسيفر (مرة واحدة):
                <div className="mt-2 flex flex-wrap gap-2">
                  <a href={TERMIUS_PLAY} target="_blank" rel="noreferrer"
                    className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/10 px-3 py-1.5 text-xs text-white hover:bg-white/20">
                    <ExternalLink className="h-3.5 w-3.5" />Termius · أندرويد
                  </a>
                  <a href={TERMIUS_IOS} target="_blank" rel="noreferrer"
                    className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/10 px-3 py-1.5 text-xs text-white hover:bg-white/20">
                    <ExternalLink className="h-3.5 w-3.5" />Termius · آيفون
                  </a>
                  <a href={PUTTY_URL} target="_blank" rel="noreferrer"
                    className="flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/10 px-3 py-1.5 text-xs text-white hover:bg-white/20">
                    <ExternalLink className="h-3.5 w-3.5" />PuTTY · ويندوز
                  </a>
                </div>
              </li>
              <li>
                في التطبيق اعمل اتصال جديد بالبيانات دي (نوع الاتصال <b dir="ltr">Telnet</b>):
                <div dir="ltr" className="mt-2 grid grid-cols-3 gap-2 text-center text-xs">
                  <span className="rounded-lg bg-black/30 p-2 text-cyan-100">{host || "IP"}</span>
                  <span className="rounded-lg bg-black/30 p-2 text-cyan-100">Port 23</span>
                  <span className="rounded-lg bg-black/30 p-2 text-cyan-100">root</span>
                </div>
                <div className="mt-2 flex flex-wrap gap-2">
                  <CopyButton text={host} label="نسخ الـ IP" />
                  {host && (
                    <a href={`telnet://${host}:23`}
                      className="flex items-center gap-2 rounded-xl border border-white/10 bg-white/10 px-4 py-2 text-sm text-white hover:bg-white/20">
                      <ExternalLink className="h-4 w-4" />جرّب فتح التطبيق
                    </a>
                  )}
                </div>
              </li>
              <li>
                بعد ما تدخل، الصق الأمر ده واضغط Enter:
                <div className="mt-2"><CopyButton text={job.command} label="نسخ الأمر" className="w-full" /></div>
              </li>
              <li>استنى لحد ما الأمر يخلص، وبعدها أعد تشغيل الواجهة (Restart GUI) أو الرسيفر لو الإضافة طلبت كده.</li>
            </ol>
            <p className="text-xs leading-6 text-slate-500">
              الرسيفر لازم يكون على نفس شبكة الواي فاي بتاعة جهازك، ولازم يكون متصل بالإنترنت عشان ينزّل الإضافة.
            </p>
            <div className="flex justify-end">
              <button onClick={onClose} className="rounded-xl border border-white/10 bg-white/10 px-4 py-2 text-sm text-white hover:bg-white/20">إغلاق</button>
            </div>
          </div>
        )}
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

  const applyLocation = useCallback((location) => {
    setSelectedCategory(location.category ?? categories[0]?.id ?? null);
    setSelectedSubCategory(location.subCategory ?? null);
    setSelectedTool(location.tool ?? null);
  }, [categories]);

  // Use the browser's native history stack so keyboard, mouse side buttons,
  // trackpad gestures, and browser Back/Forward all restore the same UI state.
  const HISTORY_STATE_KEY = "__online4techControlCenter";
  const normalizeLocation = useCallback((location) => ({
    category: categories.some((item) => item.id === location?.category)
      ? location.category
      : categories[0]?.id ?? null,
    subCategory: location?.subCategory && nodeById.has(location.subCategory)
      ? location.subCategory
      : null,
    tool: location?.tool && toolById.has(location.tool) ? location.tool : null,
  }), [categories, nodeById, toolById]);

  useEffect(() => {
    if (!categories.length) return;

    const savedLocation = window.history.state?.[HISTORY_STATE_KEY]?.location;
    const initialLocation = normalizeLocation(savedLocation || {
      category: categories[0].id,
      subCategory: null,
      tool: null,
    });

    if (!savedLocation) {
      const currentState = window.history.state && typeof window.history.state === "object"
        ? window.history.state
        : {};
      window.history.replaceState(
        { ...currentState, [HISTORY_STATE_KEY]: { location: initialLocation } },
        "",
        window.location.href
      );
    }
    applyLocation(initialLocation);

    const handlePopState = (event) => {
      const restored = event.state?.[HISTORY_STATE_KEY]?.location;
      applyLocation(normalizeLocation(restored || {
        category: categories[0].id,
        subCategory: null,
        tool: null,
      }));
      setSearchQuery("");
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [categories, normalizeLocation, applyLocation]);

  const navigateTo = useCallback((location) => {
    const nextLocation = normalizeLocation(location);
    const currentLocation = window.history.state?.[HISTORY_STATE_KEY]?.location;
    const isSameLocation = currentLocation
      && currentLocation.category === nextLocation.category
      && currentLocation.subCategory === nextLocation.subCategory
      && currentLocation.tool === nextLocation.tool;

    if (!isSameLocation) {
      const currentState = window.history.state && typeof window.history.state === "object"
        ? window.history.state
        : {};
      window.history.pushState(
        { ...currentState, [HISTORY_STATE_KEY]: { location: nextLocation } },
        "",
        window.location.href
      );
    }
    applyLocation(nextLocation);
  }, [normalizeLocation, applyLocation]);

  const goHome = useCallback(() => {
    navigateTo({ category: categories[0]?.id ?? null, subCategory: null, tool: null });
    setSearchQuery("");
  }, [categories, navigateTo]);

  const jumpToNode = useCallback((id) => {
    const n = nodeById.get(id);
    if (!n) return;
    navigateTo({ category: n.root, subCategory: n.parent ? id : null, tool: null });
  }, [nodeById, navigateTo]);

  const pickCategory = useCallback((id) => {
    navigateTo({ category: id, subCategory: null, tool: null });
  }, [navigateTo]);

  const pickNode = useCallback((id) => {
    const n = nodeById.get(id);
    if (n) navigateTo({ category: n.root, subCategory: n.parent ? id : null, tool: null });
  }, [nodeById, navigateTo]);

  const pickTool = useCallback((id) => {
    const t = toolById.get(id);
    if (!t) return;
    const n = nodeById.get(t.nodeId);
    navigateTo({ category: n.root, subCategory: n.parent ? n.id : null, tool: id });
  }, [toolById, nodeById, navigateTo]);
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
    chain.forEach((c) => list.push({ label: c.label, onClick: () => jumpToNode(c.id) }));
    if (activeTool) list.push({ label: activeTool.name, onClick: () => {} });
    return list;
  }, [activeNode, activeTool, nodeById, goHome, jumpToNode]);

  const theme = useMemo(() => themeFor(activeNode), [activeNode]);
  const centerRef = useRef(null);
  useEffect(() => { if (centerRef.current) centerRef.current.scrollTop = 0; }, [activeNode?.id]);
  const HeadIcon = theme.Icon;

  const toastTimer = useRef(null);
  const showToast = useCallback((msg) => {
    setToast(msg);
    clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(""), 1800);
  }, []);
  useEffect(() => () => clearTimeout(toastTimer.current), []);

  // Copies the Telnet install command of the selected tool.
  const handleCopy = useCallback(async (tool) => {
    const text = tool?.install || "";
    if (!text) return;
    let ok = false;
    try { await navigator.clipboard.writeText(text); ok = true; } catch { /* use the fallback below */ }
    if (!ok) {
      try {
        const ta = document.createElement("textarea");
        ta.value = text; ta.setAttribute("readonly", "");
        ta.style.cssText = "position:fixed;opacity:0;top:0;left:0";
        document.body.appendChild(ta); ta.select();
        ok = document.execCommand("copy");
        document.body.removeChild(ta);
      } catch { ok = false; }
    }
    showToast(ok ? "تم النسخ" : "تعذّر النسخ");
  }, [showToast]);

  const handleAction = useCallback((type, tool) => {
    if (onAction) return onAction(type, tool);
    const cmd = type === "install" ? tool.install : type === "update" ? tool.update || tool.install : tool.remove;
    if (!cmd) return;
    setJob({ type, tool, command: cmd });
  }, [onAction]);

  return (
    <div style={{ "--a": theme.a }} className="relative min-h-screen overflow-hidden bg-[#070a1a] text-slate-200 lg:h-screen">
      {/* ambient background: glows follow the accent color of the active section */}
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,#14183f_0%,#070a1a_60%)]" />
        <div className="cc-blob absolute -left-40 top-20 h-[520px] w-[520px] rounded-full blur-[140px]" style={{ backgroundColor: "rgb(var(--a) / .20)" }} />
        <div className="cc-blob absolute right-[-120px] top-[-80px] h-[460px] w-[460px] rounded-full blur-[140px]" style={{ backgroundColor: "rgb(var(--a) / .16)" }} />
        <div className="absolute bottom-[-160px] left-1/3 h-[420px] w-[620px] rounded-full bg-blue-700/15 blur-[150px]" />
        <div className="absolute inset-0 opacity-[.035]" style={{ backgroundImage: "linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px)", backgroundSize: "44px 44px" }} />
      </div>

      <div className="relative lg:flex lg:h-full lg:flex-col">
        <Header query={searchQuery} setQuery={setSearchQuery} results={results} onPick={pickSearch} onHome={goHome} />

        <main className="grid w-full grid-cols-1 gap-6 px-6 py-6 lg:min-h-0 lg:flex-1 lg:grid-cols-[260px_minmax(0,1fr)_360px] 2xl:grid-cols-[280px_minmax(0,1fr)_400px] lg:grid-rows-[minmax(0,1fr)] lg:overflow-hidden lg:pb-4">
          {/* Left rail */}
          <section className="cc-scroll lg:h-full lg:overflow-y-auto lg:pr-1">
            <div className="space-y-2.5 lg:pb-2">
              {categories.map((c) => (
                <CategoryCard key={c.id} node={c} active={c.id === selectedCategory} onSelect={pickCategory} />
              ))}
            </div>
          </section>

          {/* Content */}
          <section ref={centerRef} className="cc-scroll min-w-0 lg:-mx-2 lg:h-full lg:overflow-y-auto lg:px-2 lg:pb-6">
            <Breadcrumbs items={crumbs} />
            {activeNode && (
              <>
                <div className="mb-7 flex items-center gap-4">
                  <span className="cc-tile cc-tile-lg"><HeadIcon className="h-7 w-7" /></span>
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-3">
                      <h1 className="text-2xl font-semibold tracking-tight text-white">{activeNode.label}</h1>
                      <span className="cc-count">{activeNode.count}</span>
                    </div>
                    <p dir="auto" className="mt-1 text-start text-sm text-slate-400">
                      {activeNode.description || `${activeNode.count} items`}
                    </p>
                  </div>
                </div>
                <ToolGrid
                  key={activeNode.id}
                  node={activeNode}
                  theme={theme}
                  selectedToolId={selectedTool}
                  onSelectTool={pickTool}
                  onSelectNode={pickNode}
                />
              </>
            )}
          </section>

          {/* Details */}
          <section className="cc-scroll min-w-0 lg:h-full lg:overflow-y-auto">
            <DetailsPanel tool={activeTool} theme={theme} node={activeNode} onAction={handleAction} onCopy={handleCopy} />
          </section>
        </main>
      </div>

      {job && <TelnetRunner job={job} onClose={() => setJob(null)} />}
      {toast && (
        <div role="status" aria-live="polite"
          className="cc-toast fixed bottom-6 left-1/2 z-[60] flex items-center gap-2 rounded-full border border-emerald-400/30 bg-slate-900/90 px-4 py-2 text-sm text-white shadow-[0_10px_40px_rgba(0,0,0,0.5)] backdrop-blur-xl">
          {toast.startsWith("تم") && <Check className="h-4 w-4 text-emerald-300" />}
          {toast}
        </div>
      )}
    </div>
  );
}
