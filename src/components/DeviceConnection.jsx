import React, { useState } from "react";

const fieldClass = "w-full rounded-xl border border-white/10 bg-slate-950/70 px-3 py-2.5 text-sm text-white outline-none transition placeholder:text-slate-500 focus:border-cyan-400/60";
const buttonClass = "rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 px-4 py-2.5 text-sm font-semibold text-white transition hover:brightness-110 disabled:cursor-not-allowed disabled:opacity-50";

function readXmlSummary(xmlText) {
  try {
    const doc = new DOMParser().parseFromString(xmlText, "application/xml");
    if (doc.querySelector("parsererror")) return "";
    const wanted = ["e2imageversion", "e2image", "e2distroversion", "e2webifversion", "e2model", "e2devicename"];
    const values = [];
    for (const tag of wanted) {
      const node = doc.getElementsByTagName(tag)[0];
      const value = node?.textContent?.trim();
      if (value) values.push(value);
    }
    return values.join(" · ");
  } catch {
    return "";
  }
}

export default function DeviceConnection() {
  const [address, setAddress] = useState("");
  const [username, setUsername] = useState("root");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);

  async function testConnection(event) {
    event.preventDefault();
    setResult(null);

    let base;
    try {
      base = new URL(address.trim());
    } catch {
      setResult({ kind: "error", message: "اكتب عنوان HTTPS صحيح، مثال: https://192.168.1.20" });
      return;
    }

    if (base.protocol !== "https:") {
      setResult({
        kind: "warning",
        message: "المتصفح يفتح لوحة Online4Tech عبر HTTPS، وغالبًا هيمنع الاتصال برسيفر HTTP داخل الشبكة. جرّب تفعيل HTTPS في OpenWebif بشهادة موثوقة؛ وإلا هنحتاج المساعد المحلي كحل بديل.",
      });
      return;
    }
    if (base.username || base.password || base.search || base.hash) {
      setResult({ kind: "error", message: "اكتب عنوان الجهاز فقط بدون اسم مستخدم أو كلمة مرور أو إضافات في الرابط." });
      return;
    }

    base.pathname = base.pathname.replace(/\/+$/, "");
    const endpoint = new URL(`${base.pathname}/web/about`, base.origin).toString();
    setBusy(true);
    const controller = new AbortController();
    const timeoutId = window.setTimeout(() => controller.abort(), 9000);

    try {
      const token = btoa(String.fromCharCode(...new TextEncoder().encode(`${username}:${password}`)));
      const response = await fetch(endpoint, {
        method: "GET",
        headers: { Authorization: `Basic ${token}`, Accept: "application/xml, text/xml, */*" },
        cache: "no-store",
        credentials: "omit",
        redirect: "error",
        signal: controller.signal,
      });
      const body = await response.text();
      if (!response.ok) {
        setResult({ kind: "error", message: `الجهاز رد بكود HTTP ${response.status}. راجع بيانات الدخول وإعدادات OpenWebif.` });
      } else {
        setResult({
          kind: "success",
          message: "تم الوصول إلى OpenWebif بنجاح. دي أول خطوة في اكتشاف الجهاز.",
          details: readXmlSummary(body) || "تم استلام رد من الجهاز، لكن تفاصيل إصدار النظام لم تظهر في الرد.",
        });
      }
    } catch (error) {
      const aborted = error?.name === "AbortError";
      setResult({
        kind: "error",
        message: aborted
          ? "انتهت مهلة الاتصال. تأكد إن الرسيفر شغال وعلى نفس الشبكة."
          : "المتصفح منع قراءة الرد أو تعذّر الوصول للجهاز. الأسباب الشائعة: شهادة HTTPS غير موثوقة، أو CORS غير مفعّل في OpenWebif، أو الجهاز غير متاح. بيانات الدخول لم يتم حفظها.",
      });
    } finally {
      window.clearTimeout(timeoutId);
      setBusy(false);
    }
  }

  return (
    <section dir="rtl" className="mx-auto max-w-[1700px] px-6 pt-5">
      <div className="rounded-2xl border border-cyan-400/20 bg-slate-900/80 p-4 shadow-[0_12px_40px_rgba(0,0,0,0.25)] backdrop-blur-xl sm:p-5">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-white">اتصال جهاز Enigma2</h2>
            <p className="mt-1 text-xs leading-6 text-slate-400">أضف عنوان OpenWebif لاختبار الاتصال بالرسيفر من نفس الشبكة</p>
          </div>
          <span className="rounded-full border border-amber-400/20 bg-amber-400/10 px-3 py-1 text-[11px] text-amber-200">مرحلة الاختبار · قراءة فقط</span>
        </div>

        <form onSubmit={testConnection} className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-[minmax(220px,1.5fr)_1fr_1fr_auto]">
          <label className="block text-xs text-slate-300">
            عنوان الرسيفر (HTTPS)
            <input className={fieldClass + " mt-1.5"} value={address} onChange={(e) => setAddress(e.target.value)} placeholder="https://192.168.1.20" inputMode="url" autoComplete="url" required />
          </label>
          <label className="block text-xs text-slate-300">
            اسم المستخدم
            <input className={fieldClass + " mt-1.5"} value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" />
          </label>
          <label className="block text-xs text-slate-300">
            كلمة المرور
            <input className={fieldClass + " mt-1.5"} type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" />
          </label>
          <div className="flex items-end">
            <button className={buttonClass + " w-full"} type="submit" disabled={busy || !address.trim()}>
              {busy ? "جاري الاختبار..." : "اختبار الاتصال"}
            </button>
          </div>
        </form>

        <p className="mt-3 text-[11px] leading-6 text-slate-500">
          الخصوصية: بيانات الدخول تُستخدم في طلب الاختبار فقط، ولا تُحفظ في المتصفح أو تُرسل إلى خوادم Online4Tech. الاتصال المباشر يتطلب HTTPS صالحًا ودعم CORS من OpenWebif؛ لو جهازك يستخدم HTTP العادي، هنحتاج نجهّز طريقة اتصال بديلة.
        </p>

        {result && (
          <div role="status" aria-live="polite" className={`mt-4 rounded-xl border p-3 text-sm leading-7 ${
            result.kind === "success" ? "border-emerald-400/25 bg-emerald-400/10 text-emerald-200" :
            result.kind === "warning" ? "border-amber-400/25 bg-amber-400/10 text-amber-100" :
            "border-rose-400/25 bg-rose-400/10 text-rose-200"
          }`}>
            <p>{result.message}</p>
            {result.details && <p className="mt-1 text-xs opacity-80">{result.details}</p>}
          </div>
        )}
      </div>
    </section>
  );
}
