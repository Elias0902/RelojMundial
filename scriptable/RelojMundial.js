// Reloj Mundial - Scriptable widget
// Venezuela / Chile / España with day phases and Elias shift status.
// Port of https://elias0902.github.io/RelojMundial/
// Works as small / medium / large home-screen widget.

// ------------------------------------------------------------------ data

const SITE_URL = "https://elias0902.github.io/RelojMundial/";

const CITIES = [
  { id: "ve", country: "Venezuela", city: "Caracas",  tz: "America/Caracas",  flag: "🇻🇪" },
  { id: "cl", country: "Chile",     city: "Santiago", tz: "America/Santiago", flag: "🇨🇱" },
  { id: "es", country: "España",    city: "Madrid",   tz: "Europe/Madrid",    flag: "🇪🇸" }
];

// Day phases keyed by local hour [a, b). Mirrors the web app.
const PHASES = [
  { a: 0,  b: 6,  e: "🌙", n: "Durmiendo",         adv: "No escribas · solo emergencia", ok: false },
  { a: 6,  b: 9,  e: "🌅", n: "Ya despierto",      adv: "Escríbele, ya despertó",        ok: true  },
  { a: 9,  b: 12, e: "☀️", n: "Mañana activa",     adv: "Escríbele, está despierto",     ok: true  },
  { a: 12, b: 14, e: "🍽️", n: "Hora de comer",     adv: "Despierto, puedes escribirle",  ok: true  },
  { a: 14, b: 19, e: "🌤️", n: "Tarde",             adv: "Escríbele, buen momento",       ok: true  },
  { a: 19, b: 22, e: "🏠", n: "En casa",           adv: "Mejor espera a mañana",         ok: false },
  { a: 22, b: 24, e: "😴", n: "A punto de dormir",  adv: "No escribas · solo emergencia", ok: false }
];

// Elias works from Chile: shift and lunch defined in Chile local time.
const ELIAS = {
  start: new Date("2026-08-14T00:00:00-04:00").getTime(),
  wStart: 9 * 60,        // 09:00 Chile
  wEnd: 18 * 60 + 30,    // 18:30 Chile
  lunchStart: 13 * 60,   // 13:00 almuerzo
  lunchEndWeek: 14 * 60 + 30, // 14:30 lunes a jueves
  lunchEndFri: 14 * 60,  // 14:00 viernes
  tz: "America/Santiago"
};

const DOW_EN = { Sun: 0, Mon: 1, Tue: 2, Wed: 3, Thu: 4, Fri: 5, Sat: 6 };

// ------------------------------------------------------------------ palette

const COL = {
  bgTop:   new Color("#0d0d10"),
  bgBot:   new Color("#14141c"),
  card:    new Color("#1a1a22"),
  white:   new Color("#ffffff"),
  dim:     new Color("#9a9aaa"),
  dim2:    new Color("#b8b8c6"),
  ok:      new Color("#6ee7a0"),
  no:      new Color("#ffb86b"),
  accent:  new Color("#4fc3f7")
};

// ------------------------------------------------------------------ helpers

const pad = n => (n < 10 ? "0" : "") + n;

function getTime(tz) {
  const now = new Date();
  const parts = {};
  new Intl.DateTimeFormat("es-ES", {
    timeZone: tz, hour12: false, hour: "2-digit", minute: "2-digit"
  }).formatToParts(now).forEach(p => { if (p.type !== "literal") parts[p.type] = p.value; });
  let h = parseInt(parts.hour, 10);
  if (h === 24) h = 0;
  const m = parseInt(parts.minute, 10);
  const dateStr = new Intl.DateTimeFormat("es-ES", {
    timeZone: tz, weekday: "short", day: "numeric", month: "short"
  }).format(now).replace(".", "");
  const wdShort = new Intl.DateTimeFormat("en-US", { timeZone: tz, weekday: "short" }).format(now);
  return { h, m, dateStr, dow: DOW_EN[wdShort], frac: (h + m / 60) / 24 };
}

function phaseFor(h) {
  for (const p of PHASES) if (h >= p.a && h < p.b) return p;
  return PHASES[0];
}

function fmtHM(mins) {
  const h = Math.floor(mins / 60);
  const m = Math.floor(mins % 60);
  return h > 0 ? h + "h " + pad(m) + "m" : m + "m";
}

function eliasInfo() {
  const nowMs = Date.now();
  if (nowMs < ELIAS.start) {
    const diff = ELIAS.start - nowMs;
    const d = Math.floor(diff / 86400000);
    return { status: "⏳ Por comenzar", line1: "Comienza el 14 de agosto 2026",
             line2: "Faltan " + d + " días", pct: 0, ok: false };
  }
  const cl = getTime(ELIAS.tz);
  const mins = cl.h * 60 + cl.m;
  const dow = cl.dow;                     // 0=domingo … 6=sábado
  const pct = ((mins - ELIAS.wStart) / (ELIAS.wEnd - ELIAS.wStart)) * 100;

  // Fin de semana: no hay turno
  if (dow === 0 || dow === 6) {
    return { status: "😴 Descansando", line1: "Fin de semana · sin turno",
             line2: "Vuelve el lunes 09:00", pct: 0, ok: false };
  }

  // Almuerzo (13:00 – 14:30 lun-jue, 13:00 – 14:00 vie), hora de Chile
  const lunchEnd = (dow === 5) ? ELIAS.lunchEndFri : ELIAS.lunchEndWeek;
  if (mins >= ELIAS.lunchStart && mins < lunchEnd) {
    return { status: "🍽️ Almorzando", line1: "En almuerzo · puedes escribirle",
             line2: "Vuelve en " + fmtHM(lunchEnd - mins), pct: pct, ok: true };
  }

  // Trabajando
  if (mins >= ELIAS.wStart && mins < ELIAS.wEnd) {
    return { status: "💼 Trabajando", line1: "Turno 09:00 – 18:30 · hora de Chile",
             line2: "Quedan " + fmtHM(ELIAS.wEnd - mins), pct: pct, ok: true };
  }

  // Fuera de horario
  if (mins < ELIAS.wStart) {
    return { status: "😴 Descansando", line1: "Próximo turno 09:00 · hora de Chile",
             line2: "En " + fmtHM(ELIAS.wStart - mins), pct: 0, ok: false };
  }
  return { status: "😴 Descansando", line1: "Turno terminado · hora de Chile",
           line2: (dow === 5) ? "Vuelve el lunes 09:00" : "Vuelve mañana 09:00",
           pct: 0, ok: false };
}

// ------------------------------------------------------------------ ui blocks

function cityColumn(parent, c, big) {
  const t = getTime(c.tz);
  const ph = phaseFor(t.h);

  const col = parent.addStack();
  col.layoutVertically();
  col.spacing = 1;

  const head = col.addStack();
  head.centerAlignContent();
  head.addText(c.flag).font = Font.systemFont(big ? 15 : 13);
  head.addSpacer(4);
  const co = head.addText(c.country);
  co.font = Font.mediumSystemFont(big ? 12 : 11);
  co.textColor = COL.dim2;

  const tm = col.addText(pad(t.h) + ":" + pad(t.m));
  tm.font = Font.boldSystemFont(big ? 30 : 26);
  tm.textColor = COL.white;

  const dt = col.addText(t.dateStr);
  dt.font = Font.systemFont(9);
  dt.textColor = COL.dim;

  col.addSpacer(3);

  const pr = col.addStack();
  pr.centerAlignContent();
  pr.addText(ph.e).font = Font.systemFont(12);
  pr.addSpacer(3);
  const pn = pr.addText(ph.n);
  pn.font = Font.mediumSystemFont(10);
  pn.textColor = COL.dim;

  const av = col.addText(ph.adv);
  av.font = Font.mediumSystemFont(9);
  av.textColor = ph.ok ? COL.ok : COL.no;
  av.lineLimit = 2;

  return col;
}

function cityRow(parent, c) {
  const t = getTime(c.tz);
  const ph = phaseFor(t.h);

  const row = parent.addStack();
  row.centerAlignContent();

  row.addText(c.flag).font = Font.systemFont(15);
  row.addSpacer(6);

  const tm = row.addText(pad(t.h) + ":" + pad(t.m));
  tm.font = Font.boldSystemFont(17);
  tm.textColor = COL.white;

  row.addSpacer();

  const pe = row.addText(ph.e);
  pe.font = Font.systemFont(15);
}

// Small widget showing a single city large (used with parameter "chile").
function singleCityCard(w, c) {
  const t = getTime(c.tz);
  const ph = phaseFor(t.h);

  const head = w.addStack();
  head.centerAlignContent();
  head.addText(c.flag).font = Font.systemFont(17);
  head.addSpacer(5);
  const co = head.addText(c.country);
  co.font = Font.boldSystemFont(14);
  co.textColor = COL.white;
  w.addSpacer(4);

  const tm = w.addText(pad(t.h) + ":" + pad(t.m));
  tm.font = Font.boldSystemFont(42);
  tm.textColor = COL.white;

  const dt = w.addText(t.dateStr + " · " + c.city);
  dt.font = Font.systemFont(10);
  dt.textColor = COL.dim;
  w.addSpacer(8);

  const pr = w.addStack();
  pr.centerAlignContent();
  pr.addText(ph.e).font = Font.systemFont(15);
  pr.addSpacer(4);
  const pn = pr.addText(ph.n);
  pn.font = Font.mediumSystemFont(12);
  pn.textColor = COL.dim2;
  w.addSpacer(2);

  const av = w.addText(ph.adv);
  av.font = Font.boldSystemFont(12);
  av.textColor = ph.ok ? COL.ok : COL.no;
  av.lineLimit = 2;
}

// Small widget fully dedicated to Elias' shift status (parameter "elias").
function singleEliasCard(w) {
  const e = eliasInfo();

  const head = w.addStack();
  head.centerAlignContent();
  head.addText("🇨🇱").font = Font.systemFont(17);
  head.addSpacer(5);
  const tag = head.addText("ELIAS");
  tag.font = Font.heavySystemFont(14);
  tag.textColor = COL.white;
  w.addSpacer(6);

  const st = w.addText(e.status);
  st.font = Font.boldSystemFont(20);
  st.textColor = e.ok ? COL.ok : COL.no;
  w.addSpacer(6);

  const l1 = w.addText(e.line1);
  l1.font = Font.systemFont(11);
  l1.textColor = COL.dim;
  w.addSpacer(1);

  const l2 = w.addText(e.line2);
  l2.font = Font.boldSystemFont(15);
  l2.textColor = COL.white;

  // Progress bar (only meaningful while working).
  if (e.pct > 0) {
    w.addSpacer(8);
    const track = w.addStack();
    track.backgroundColor = COL.card;
    track.cornerRadius = 3;
    track.size = new Size(130, 6);
    const fill = track.addStack();
    fill.backgroundColor = COL.ok;
    fill.cornerRadius = 3;
    fill.size = new Size(Math.max(4, 130 * e.pct / 100), 6);
  }
}

function eliasBlock(parent) {
  const e = eliasInfo();
  const box = parent.addStack();
  box.layoutVertically();
  box.backgroundColor = COL.card;
  box.cornerRadius = 10;
  box.setPadding(8, 10, 8, 10);
  box.spacing = 2;

  const top = box.addStack();
  top.centerAlignContent();
  const tag = top.addText("🇨🇱 ELIAS");
  tag.font = Font.heavySystemFont(11);
  tag.textColor = COL.dim2;
  top.addSpacer();
  const st = top.addText(e.status);
  st.font = Font.boldSystemFont(11);
  st.textColor = e.ok ? COL.ok : COL.no;

  const l1 = box.addText(e.line1);
  l1.font = Font.systemFont(10);
  l1.textColor = COL.dim;

  const l2 = box.addText(e.line2);
  l2.font = Font.mediumSystemFont(12);
  l2.textColor = COL.white;
}

// ------------------------------------------------------------------ build

function header(w) {
  const h = w.addStack();
  h.centerAlignContent();
  const t = h.addText("🕑  Reloj Mundial");
  t.font = Font.boldSystemFont(13);
  t.textColor = COL.white;
}

function buildWidget(family, param) {
  const w = new ListWidget();
  const g = new LinearGradient();
  g.colors = [COL.bgTop, COL.bgBot];
  g.locations = [0, 1];
  w.backgroundGradient = g;
  w.setPadding(14, 14, 14, 14);
  w.url = SITE_URL; // tapping the widget opens the full app

  if (family === "small") {
    // Parameter decides what the small widget shows:
    //   "chile" / "cl" -> only Chile   |   "elias" -> only Elias' shift
    //   empty / other  -> the three cities compact
    if (param === "chile" || param === "cl") {
      singleCityCard(w, CITIES.find(c => c.id === "cl"));
    } else if (param === "elias" || param === "elías") {
      singleEliasCard(w);
    } else {
      header(w);
      w.addSpacer(6);
      const list = w.addStack();
      list.layoutVertically();
      list.spacing = 7;
      CITIES.forEach(c => cityRow(list, c));
    }
  } else if (family === "large") {
    header(w);
    w.addSpacer(10);
    const cols = w.addStack();
    cols.spacing = 6;
    CITIES.forEach((c, i) => {
      cityColumn(cols, c, true);
      if (i < CITIES.length - 1) cols.addSpacer();
    });
    w.addSpacer();
    eliasBlock(w);
  } else {
    // medium (default)
    const cols = w.addStack();
    cols.spacing = 6;
    CITIES.forEach((c, i) => {
      cityColumn(cols, c, false);
      if (i < CITIES.length - 1) cols.addSpacer();
    });
  }

  // Hint iOS to refresh; the system decides the real cadence.
  w.refreshAfterDate = new Date(Date.now() + 5 * 60 * 1000);
  return w;
}

// ------------------------------------------------------------------ run

const family = config.widgetFamily || "medium";
const param = (args.widgetParameter || "").toString().trim().toLowerCase();
const widget = buildWidget(family, param);

if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  // When run inside the app, preview the small variant so you can test the
  // parameter: set it below to "chile" or "elias" to preview those.
  if (family === "small") widget.presentSmall();
  else if (family === "large") widget.presentLarge();
  else widget.presentMedium();
}
Script.complete();
