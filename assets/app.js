/* Reloj Mundial - landing/widget
   Fases del dia por ciudad, animacion dia/noche, timeline 24h
   y widget de Elias (Chile): comienza a trabajar el 14 ago 2026,
   turno 09:00 - 18:30 hora Venezuela. */
(function () {
  "use strict";

  var CITIES = [
    { id: "ve", country: "Venezuela", city: "Caracas",  tz: "America/Caracas",  off: -4, flag: "ve" },
    { id: "cl", country: "Chile",     city: "Santiago", tz: "America/Santiago", off: -4, flag: "cl" },
    { id: "es", country: "España",    city: "Madrid",   tz: "Europe/Madrid",    off: +2, flag: "es" }
  ];

  var PHASES = [
    { a: 0,  b: 6,  e: "🌙", n: "Durmiendo",         m: "Está durmiendo: no le escribas salvo emergencia",      adv: "No escribas · solo emergencia", ok: false, c: "rgba(59,76,202,.55)" },
    { a: 6,  b: 9,  e: "🌅", n: "Ya despierto",      m: "Ya despertó: puedes escribirle",                         adv: "Escríbele, ya despertó", ok: true, c: "rgba(255,165,0,.55)" },
    { a: 9,  b: 12, e: "☀️", n: "Mañana activa",     m: "Está despierto: escríbele sin problema",                 adv: "Escríbele, está despierto", ok: true, c: "rgba(255,215,0,.5)" },
    { a: 12, b: 14, e: "🍽️", n: "Hora de comer",     m: "Está comiendo, pero despierto: puedes escribirle",       adv: "Despierto, puedes escribirle", ok: true, c: "rgba(255,107,107,.6)" },
    { a: 14, b: 19, e: "🌤️", n: "Tarde",             m: "Está despierto: buen momento para escribirle",           adv: "Escríbele, buen momento", ok: true, c: "rgba(79,195,247,.5)" },
    { a: 19, b: 22, e: "🏠", n: "En casa",            m: "En casa, a punto de dormir: mejor esperar a mañana",     adv: "Mejor espera a mañana", ok: false, c: "rgba(171,71,188,.55)" },
    { a: 22, b: 24, e: "😴", n: "A punto de dormir",  m: "Casi durmiendo: solo escríbele si es una emergencia",   adv: "No escribas · solo emergencia", ok: false, c: "rgba(92,107,192,.55)" }
  ];

  var ELIAS = {
    start: new Date("2026-08-14T00:00:00-04:00").getTime(),
    wStart: 9 * 60,          // 09:00
    wEnd: 18 * 60 + 30,      // 18:30
    tz: "America/Caracas",
    off: -4
  };

  var WEEKDAYS = ["domingo", "lunes", "martes", "miércoles", "jueves", "viernes", "sábado"];
  var MONTHS = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

  function pad(n) { return (n < 10 ? "0" : "") + n; }

  function flagClass(id) { return "flag-" + id; }

  /* ---- hora en una zona (Intl con respaldo por offset UTC) ---- */
  function getTime(city) {
    var now = new Date();
    try {
      var parts = {};
      new Intl.DateTimeFormat("en-GB", {
        timeZone: city.tz, hour12: false,
        hour: "2-digit", minute: "2-digit", second: "2-digit",
        day: "2-digit", month: "2-digit", year: "numeric", weekday: "long"
      }).formatToParts(now).forEach(function (p) {
        if (p.type !== "literal") parts[p.type] = p.value;
      });
      var h = parseInt(parts.hour, 10);
      if (h === 24) h = 0;
      return {
        h: h,
        m: parseInt(parts.minute, 10),
        s: parseInt(parts.second, 10),
        day: parseInt(parts.day, 10),
        month: parseInt(parts.month, 10),
        year: parseInt(parts.year, 10),
        weekday: parts.weekday,
        frac: (h + parseInt(parts.minute, 10) / 60 + parseInt(parts.second, 10) / 3600) / 24
      };
    } catch (e) {
      var d = new Date(now.getTime() + city.off * 3600000);
      var wd = d.getUTCDay();
      return {
        h: d.getUTCHours(),
        m: d.getUTCMinutes(),
        s: d.getUTCSeconds(),
        day: d.getUTCDate(),
        month: d.getUTCMonth() + 1,
        year: d.getUTCFullYear(),
        weekday: WEEKDAYS[wd],
        frac: (d.getUTCHours() + d.getUTCMinutes() / 60 + d.getUTCSeconds() / 3600) / 24
      };
    }
  }

  function phaseFor(frac) {
    var h = frac * 24;
    for (var i = 0; i < PHASES.length; i++) {
      if (h >= PHASES[i].a && h < PHASES[i].b) return PHASES[i];
    }
    return PHASES[0];
  }

  /* ---- cielo: sol/luna sobre un arco + factor de luz ---- */
  function skyPos(frac) {
    var x, y, kind, dayFactor;
    if (frac >= 0.25 && frac <= 0.75) {
      var t = (frac - 0.25) / 0.5;
      var a = Math.PI - t * Math.PI;
      x = 50 + 40 * Math.cos(a);
      y = 88 - 72 * Math.sin(a);
      kind = "sun";
      dayFactor = Math.sin(t * Math.PI);
    } else if (frac >= 0.75) {
      var t2 = (frac - 0.75) / 0.25;
      var a2 = Math.PI * t2;
      x = 50 + 40 * Math.cos(a2);
      y = 88 - 72 * Math.sin(a2);
      kind = "moon";
      dayFactor = 0;
    } else {
      var t3 = frac / 0.25;
      var a3 = Math.PI - Math.PI * t3;
      x = 50 - 40 * Math.cos(a3);
      y = 88 - 72 * Math.sin(a3);
      kind = "moon";
      dayFactor = 0;
    }
    return { x: x, y: y, kind: kind, dayFactor: dayFactor };
  }

  function hex(n) { return (n < 16 ? "0" : "") + n.toString(16); }
  function mix(c1, c2, f) {
    var p1 = [parseInt(c1.slice(1, 3), 16), parseInt(c1.slice(3, 5), 16), parseInt(c1.slice(5, 7), 16)];
    var p2 = [parseInt(c2.slice(1, 3), 16), parseInt(c2.slice(3, 5), 16), parseInt(c2.slice(5, 7), 16)];
    return "#" + [0, 1, 2].map(function (i) {
      return hex(Math.round(p1[i] + (p2[i] - p1[i]) * f));
    }).join("");
  }

  function skyGradient(dayFactor) {
    var DAY_TOP = "#0e7dd4", DAY_BOT = "#9fd8ff";
    var NIGHT_TOP = "#06061a", NIGHT_BOT = "#141430";
    var top = mix(NIGHT_TOP, DAY_TOP, dayFactor);
    var bot = mix(NIGHT_BOT, DAY_BOT, dayFactor);
    if (dayFactor > 0.02 && dayFactor < 0.45) {
      var d = Math.sin((dayFactor / 0.45) * Math.PI);
      top = mix(top, "#2b1055", 0.35 * d);
      bot = mix(bot, "#f59a6b", 0.55 * d);
    }
    return "linear-gradient(180deg," + top + "," + bot + ")";
  }

  /* ---- construccion ---- */
  function buildDaybarTrack(track) {
    PHASES.forEach(function (p) {
      var seg = document.createElement("i");
      seg.className = "seg";
      seg.style.background = p.c;
      seg.style.left = (p.a / 24 * 100) + "%";
      seg.style.width = ((p.b - p.a) / 24 * 100) + "%";
      track.insertBefore(seg, track.firstChild);
    });
  }

  function buildLive() {
    var track = document.getElementById("liveTrack");
    track.innerHTML = "";
    CITIES.forEach(function (c, idx) {
      var lane = document.createElement("div");
      lane.className = "live-lane";
      lane.style.top = (idx * 100 / CITIES.length) + "%";
      lane.style.height = (100 / CITIES.length) + "%";
      var label = document.createElement("div");
      label.className = "lane-label";
      var flag = document.createElement("span");
      flag.className = "flag " + flagClass(c.flag) + " lane-flag";
      var name = document.createElement("span");
      name.textContent = c.country;
      label.appendChild(flag);
      label.appendChild(name);
      var segs = document.createElement("div");
      segs.className = "lane-segs";
      PHASES.forEach(function (p) {
        var s = document.createElement("i");
        s.style.background = p.c;
        s.style.left = (p.a / 24 * 100) + "%";
        s.style.width = ((p.b - p.a) / 24 * 100) + "%";
        segs.appendChild(s);
      });
      var ptr = document.createElement("i");
      ptr.className = "lane-ptr";
      lane.appendChild(label);
      lane.appendChild(segs);
      lane.appendChild(ptr);
      track.appendChild(lane);
      c._ptr = ptr;
    });
  }

  function buildLegend() {
    var el = document.querySelector(".phase-legend");
    PHASES.forEach(function (p) {
      var s = document.createElement("span");
      s.innerHTML = "<i>" + p.e + "</i> <b>" + p.n + "</b> " + p.adv;
      s.classList.add(p.ok ? "ok" : "no");
      el.appendChild(s);
    });
  }

  /* ---- elias (chile) ---- */
  function fmtClock(min) {
    var h = Math.floor(min / 60);
    var m = Math.floor(min % 60);
    var s = Math.floor((min * 60) % 60);
    return pad(h) + ":" + pad(m) + ":" + pad(s);
  }

  function eliasInfo() {
    var nowMs = Date.now();
    if (nowMs < ELIAS.start) {
      var diff = ELIAS.start - nowMs;
      var d = Math.floor(diff / 86400000);
      var rest = Math.floor(diff / 1000) % 86400;
      var hh = Math.floor(rest / 3600);
      var mm = Math.floor((rest % 3600) / 60);
      var ss = rest % 60;
      return {
        state: "count",
        status: "⏳ Por comenzar",
        line1: "Comienza a trabajar el 14 de agosto 2026",
        line2: pad(d) + "d " + pad(hh) + ":" + pad(mm) + ":" + pad(ss),
        pct: null
      };
    }
    var ve = getTime(ELIAS);
    var mins = ve.h * 60 + ve.m + ve.s / 60;
    if (mins >= ELIAS.wStart && mins < ELIAS.wEnd) {
      return {
        state: "work",
        status: "💼 Trabajando",
        line1: "Turno 09:00 – 18:30 · hora Venezuela",
        line2: "Quedan " + fmtClock(ELIAS.wEnd - mins),
        pct: ((mins - ELIAS.wStart) / (ELIAS.wEnd - ELIAS.wStart)) * 100
      };
    }
    var rem = mins < ELIAS.wStart ? ELIAS.wStart - mins : 24 * 60 - mins + ELIAS.wStart;
    return {
      state: "rest",
      status: "😴 Descansando",
      line1: "Próximo turno a las 09:00 · hora Venezuela",
      line2: "En " + fmtClock(rem),
      pct: null
    };
  }

  function fmtDate(t) {
    return WEEKDAYS[t.weekday] + " " + t.day + " de " + MONTHS[t.month - 1] + " de " + t.year;
  }

  /* ---- pintado ---- */
  function render() {
    var elias = eliasInfo();

    CITIES.forEach(function (c) {
      var t = getTime(c);
      var card = document.querySelector('.card[data-city="' + c.id + '"]');
      var phase = phaseFor(t.frac);
      var sp = skyPos(t.frac);

      card.querySelector(".clock").textContent = pad(t.h) + ":" + pad(t.m) + ":" + pad(t.s);
      card.querySelector(".date").textContent = fmtDate(t);
      card.querySelector(".phase-name").textContent = phase.n;
      card.querySelector(".phase-emoji").textContent = phase.e;
      card.querySelector(".phase-now").textContent = phase.e + " " + phase.n + " · " + pad(t.h) + ":" + pad(t.m);

      var badge = card.querySelector(".phase-badge");
      badge.classList.toggle("ok", phase.ok);
      badge.classList.toggle("no", !phase.ok);

      var adv = card.querySelector(".advice");
      adv.classList.toggle("ok", phase.ok);
      adv.classList.toggle("no", !phase.ok);
      adv.querySelector(".adv-txt").textContent = phase.adv;

      var sky = card.querySelector(".sky");
      sky.classList.toggle("night", t.frac < 0.25 || t.frac > 0.75);
      sky.style.background = skyGradient(sp.dayFactor);
      var sun = sky.querySelector(".sun"), moon = sky.querySelector(".moon");
      sun.style.left = sp.x + "%";
      sun.style.top = sp.y + "%";
      sun.style.opacity = sp.kind === "sun" ? 1 : 0;
      moon.style.left = sp.x + "%";
      moon.style.top = sp.y + "%";
      moon.style.opacity = sp.kind === "moon" ? 1 : 0;
      sky.querySelector(".sky-label").textContent = phase.m;

      card.querySelector(".daybar-ptr").style.left = (t.frac * 100) + "%";
      card.querySelector(".daybar-legend").innerHTML =
        "<span class='phase-now'>" + phase.e + "</span> " + phase.n + " en " + c.city;

      if (c._ptr) {
        c._ptr.style.left = (t.frac * 100) + "%";
      }

      if (c.id === "cl") {
        var el = card.querySelector(".elias");
        var statusEl = el.querySelector(".elias-status");
        statusEl.textContent = elias.status;
        statusEl.className = "elias-status " + elias.state;
        el.querySelector(".elias-line1").textContent = elias.line1;
        el.querySelector(".elias-line2").textContent = elias.line2;
        var bar = el.querySelector(".elias-bar i");
        bar.style.width = (elias.pct !== null ? elias.pct : 0) + "%";
      }
    });

    updateIcon(getTime(CITIES[0]));
  }

  /* ---- icono del reloj animado (manecillas en vivo) ---- */
  function updateIcon(t) {
    var now = new Date();
    var hDeg = (t.h % 12) * 30 + t.m * 0.5 + t.s * (1 / 120);
    var mDeg = t.m * 6 + t.s * 0.1;
    var sDeg = t.s * 6 + now.getMilliseconds() * 0.006;
    var hands = document.querySelectorAll(".ico-hands line");
    hands[0].style.transform = "rotate(" + sDeg + "deg)";
    hands[1].style.transform = "rotate(" + mDeg + "deg)";
    hands[2].style.transform = "rotate(" + hDeg + "deg)";
  }

  /* ---- modo widget ---- */
  function setWidget(on) {
    document.body.classList.toggle("widget", on);
    try { localStorage.setItem("rmWidget", on ? "1" : "0"); } catch (e) {}
    document.getElementById("widgetBtn").textContent = on ? "☰ Modo landing" : "▣ Modo widget";
  }

  function init() {
    document.querySelectorAll(".daybar-track").forEach(buildDaybarTrack);
    buildLive();
    buildLegend();

    var wantWidget = false;
    try { wantWidget = localStorage.getItem("rmWidget") === "1"; } catch (e) {}
    if (/[?&]widget/.test(window.location.search)) wantWidget = true;
    setWidget(wantWidget);

    document.getElementById("widgetBtn").addEventListener("click", function () {
      setWidget(!document.body.classList.contains("widget"));
    });

    render();
    setInterval(render, 250);

    /* Service worker (instalable + offline) */
    if ("serviceWorker" in navigator && window.location.protocol === "https:") {
      navigator.serviceWorker.register("./sw.js").catch(function () {});
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
