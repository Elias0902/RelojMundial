#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reloj Mundial - Widget de escritorio
Hora local de Venezuela, Chile y Espana, con banderas.

Interfaz al estilo iOS:
  - Panel de ajustes visual (boton de engranaje arriba a la derecha):
      * Paleta de color arrastrable (arcoiris) para el color del texto.
      * Slider de intensidad del color.
      * Slider de grosor de la letra (fina <-> gruesa).
      * Selector de tipografia.
      * Selector de fondo (degradados) y fondo transparente.
  - Botones arriba a la derecha: Ajustes / Pantalla completa / Pequeno.
  - Redimension manual arrastrando la esquina inferior derecha.
  - Modo anclado al escritorio (no es ventana emergente) o flotante.

Config en: %APPDATA%\\RelojMundial\\config.json
"""

import os
import sys
import json
import time
import math
import colorsys
import tkinter as tk
from tkinter import font as tkfont
from datetime import datetime, timezone, timedelta

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

IS_WIN = sys.platform.startswith("win")
if IS_WIN:
    import ctypes

# (Pais, Ciudad, Zona IANA, offset de respaldo)
CITIES = [
    ("Venezuela", "Caracas",  "America/Caracas",  -4),
    ("Chile",     "Santiago", "America/Santiago", -4),
    ("Espana",    "Madrid",   "Europe/Madrid",    +2),
]

# Fases del dia (hora local de cada ciudad):
# (h_inicio, h_fin, emoji, nombre, consejo, ok)  -> ok=True: buen momento para escribir
# Los mensajes son los mismos que muestra la web (index.html / assets).
PHASES = [
    (0,  6,  "\U0001F319", "Durmiendo",         "Est\u00E1 durmiendo: no le escribas salvo emergencia", False),
    (6,  9,  "\U0001F305", "Ya despierto",      "Ya despert\u00F3: puedes escribirle",                   True),
    (9,  12, "\u2600\uFE0F", "Ma\u00F1ana activa",   "Est\u00E1 despierto: escr\u00EDbele sin problema",           True),
    (12, 14, "\U0001F37D\uFE0F", "Hora de comer", "Est\u00E1 comiendo, pero despierto: puedes escribirle", True),
    (14, 19, "\U0001F324\uFE0F", "Tarde",       "Est\u00E1 despierto: buen momento para escribirle",     True),
    (19, 22, "\U0001F3E0", "En casa",           "En casa, a punto de dormir: mejor esperar a ma\u00F1ana", False),
    (22, 24, "\U0001F634", "A punto de dormir", "Casi durmiendo: solo escr\u00EDbele si es una emergencia", False),
]
# Colores de la barra de 24h por fase (indican el momento del dia).
PHASE_COLORS = ["#3B4CCA", "#FFA500", "#FFD700", "#FF6B6B",
                "#4FC3F7", "#AB47BC", "#5C6BC0"]
# Acentos suaves para el consejo: verde si conviene escribir, ambar si no.
ADVICE_OK = "#8BE99A"
ADVICE_NO = "#FFB86B"

# Elias (Chile): comienza a trabajar el 14 de agosto de 2026.
# Turno de 09:00 a 18:30, hora de Venezuela.
ELIAS_YEAR, ELIAS_MONTH, ELIAS_DAY = 2026, 8, 14
ELIAS_WORK = (9 * 60, 18 * 60 + 30)          # (inicio, fin) en minutos
ELIAS_TZ, ELIAS_OFF = "America/Caracas", -4

# Fondos con degradado (g1 arriba -> g2 abajo)
BACKGROUNDS = {
    "Aurora":     ("#12C2E9", "#C471ED"),
    "Atardecer":  ("#FF512F", "#DD2476"),
    "Neon":       ("#0F0C29", "#302B63"),
    "Tropical":   ("#F6D365", "#FDA085"),
    "Oceano":     ("#2193B0", "#6DD5ED"),
    "Bosque":     ("#134E5E", "#71B280"),
    "Fuego":      ("#F12711", "#F5AF19"),
    "Uva":        ("#4568DC", "#B06AB3"),
    "Menta":      ("#00B09B", "#96C93D"),
    "Cielo":      ("#2980B9", "#6DD5FA"),
    "Medianoche": ("#0B0B14", "#1A1A2E"),
    "Grafito":    ("#232526", "#414345"),
    "Nieve":      ("#FFFFFF", "#E6E9F0"),
}

# Colores rapidos para el texto (paleta de swatches)
SWATCHES = [
    "#FFFFFF", "#111111", "#FFD1DC", "#7FE7FF", "#8AB4FF", "#C7A6FF",
    "#E39BE0", "#FF6B6B", "#FFB86B", "#FFE45E", "#8BE99A", "#00F5D4",
]

FONTS = ["Segoe UI", "Bahnschrift", "Consolas", "Cascadia Code",
         "Verdana", "Georgia", "Impact"]

DEFAULT_CONFIG = {
    "font": "Segoe UI",
    "weight": 1,                 # 0 fina .. 3 gruesa
    "scale": 1.0,
    "size_mode": "manual",       # manual | fullscreen
    "orientation": "vertical",
    "alpha": 1.0,
    "desktop_mode": True,
    "always_on_top": False,
    "glue_wallpaper": False,     # pegar al fondo de pantalla (tras todo)
    "transparent_bg": False,
    "show_seconds": True,
    "show_date": True,
    "show_flags": True,
    "hour24": True,
    "bg": "Grafito",             # neutral por defecto (gris grafito)
    "bg_g1": "#232526",
    "bg_g2": "#414345",
    "txt_hue": 0.0,              # 0..360
    "txt_sat": 0.0,              # 0..1  (0 = blanco)
    "txt_val": 1.0,              # 0..1
    "x": 80,
    "y": 80,
}

TKEY = "#010101"


def config_dir():
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    d = os.path.join(base, "RelojMundial")
    os.makedirs(d, exist_ok=True)
    return d


CONFIG_PATH = os.path.join(config_dir(), "config.json")


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg.update(json.load(f))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def hsv_hex(h, s, v):
    r, g, b = colorsys.hsv_to_rgb((h % 360) / 360.0, max(0, min(1, s)), max(0, min(1, v)))
    return "#%02x%02x%02x" % (int(r * 255), int(g * 255), int(b * 255))


def rgb_of(hexc):
    hexc = hexc.lstrip("#")
    return int(hexc[0:2], 16), int(hexc[2:4], 16), int(hexc[4:6], 16)


def hex_to_hsv(hexc):
    r, g, b = rgb_of(hexc)
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    return h * 360.0, s, v


def interp(c1, c2, f):
    r1, g1, b1 = rgb_of(c1)
    r2, g2, b2 = rgb_of(c2)
    return "#%02x%02x%02x" % (int(r1 + (r2 - r1) * f),
                              int(g1 + (g2 - g1) * f),
                              int(b1 + (b2 - b1) * f))


def lum(hexc):
    r, g, b = rgb_of(hexc)
    return (0.299 * r + 0.587 * g + 0.114 * b) / 255.0


class ClockWidget:
    def __init__(self, root, front=False):
        self.root = root
        self.cfg = load_config()
        self.force_front = front      # --front: siempre visible / al frente
        self._settled = False         # tras el arranque pasa al fondo
        self._glued = False           # pegado al WorkerW (fondo de pantalla)
        self._mode = None
        self._start = None
        self.view = "clock"          # "clock" (reloj) | "horarios" (fases del dia)
        self.items = []
        self.buttons = []
        self.settings = None
        self.cw = self.ch = 0
        self._prev = None

        root.title("Reloj Mundial")
        root.overrideredirect(True)
        try:
            root.attributes("-alpha", self.cfg["alpha"])
        except Exception:
            pass

        self.canvas = tk.Canvas(root, highlightthickness=0, bd=0)
        self.canvas.pack(fill="both", expand=True)

        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<B1-Motion>", self._motion)
        self.canvas.bind("<ButtonRelease-1>", self._release)
        self.canvas.bind("<Button-3>", self._popup)
        root.bind("<Escape>", lambda e: self._exit_fullscreen())
        root.bind("h", lambda e: self._toggle_view())
        root.bind("H", lambda e: self._toggle_view())

        self.menu = tk.Menu(root, tearoff=0)
        self._build_menu()

        self.apply_window_mode()
        self.redraw()
        self._tick()
        try:
            self.root.lift()
        except Exception:
            pass
        # Al arrancar se muestra al frente unos segundos y luego, en modo
        # escritorio, pasa al fondo. Asi siempre se nota que abrio.
        self.root.after(4000, self._settle)

    # ------------------------------------------------------- color de texto
    def text_colors(self):
        h, s, v = self.cfg["txt_hue"], self.cfg["txt_sat"], self.cfg["txt_val"]
        time = hsv_hex(h, s, v)
        accent = hsv_hex(h, min(1.0, s + 0.35), v) if s > 0.05 else time
        city = hsv_hex(h, s * 0.55, min(1.0, v + 0.05)) if s > 0.05 else time
        sub = hsv_hex(h, s * 0.4, v)
        shadow = "#000000" if lum(time) > 0.4 else "#FFFFFF"
        return {"time": time, "accent": accent, "city": city, "sub": sub, "shadow": shadow}

    def bg_colors(self):
        if self.cfg["bg"] == "custom":
            return self.cfg["bg_g1"], self.cfg["bg_g2"]
        return BACKGROUNDS.get(self.cfg["bg"], BACKGROUNDS["Grafito"])

    # ---------------------------------------------------------------- fuente
    def make_font(self, size, role):
        base = self.cfg["font"]
        w = int(self.cfg["weight"])
        if base.startswith("Segoe UI"):
            if role == "time":
                fam = ["Segoe UI Light", "Segoe UI", "Segoe UI Semibold", "Segoe UI Black"][max(0, min(3, w))]
            elif role == "country":
                fam = "Segoe UI Semibold"
            else:
                fam = "Segoe UI"
            return tkfont.Font(family=fam, size=size)
        wt = "bold" if (role == "country" or (role == "time" and w >= 2)) else "normal"
        return tkfont.Font(family=base, size=size, weight=wt)

    # ---------------------------------------------------------------- layout
    def compute_layout(self, s):
        f_country = self.make_font(max(8, int(11 * s)), "country")
        f_time = self.make_font(max(14, int(34 * s)), "time")
        f_sub = self.make_font(max(7, int(9 * s)), "sub")
        lh_c = f_country.metrics("linespace")
        lh_t = f_time.metrics("linespace")
        lh_s = f_sub.metrics("linespace")

        flag_h = lh_c if self.cfg["show_flags"] else 0
        flag_w = int(flag_h * 1.5) if self.cfg["show_flags"] else 0
        fgap = int(6 * s) if self.cfg["show_flags"] else 0

        tsample = "00:00:00" if self.cfg["hour24"] else "00:00:00 PM"
        block_w = 0
        for country, city, tz, off in CITIES:
            cw = flag_w + fgap + f_country.measure(country.upper())
            block_w = max(block_w, cw, f_time.measure(tsample),
                          f_sub.measure("%s . Xxx 00 Xxx  (aprox.)" % city))

        pad = int(14 * s)
        gap = int(12 * s)
        ctrl_r = max(8, int(9 * s))
        topbar = ctrl_r * 2 + int(10 * s)
        block_h = lh_c + lh_t + lh_s + int(6 * s)

        min_w = int(ctrl_r * 2 * 4 + 40 * s)  # espacio para 4 botones
        if self.cfg["orientation"] == "horizontal":
            cw = pad * 2 + block_w * len(CITIES) + gap * (len(CITIES) - 1)
            ch = topbar + block_h + pad
        else:
            cw = pad * 2 + block_w
            ch = topbar + block_h * len(CITIES) + gap * (len(CITIES) - 1) + pad
        cw = max(cw, min_w)

        return {"W": cw, "H": ch, "pad": pad, "gap": gap, "topbar": topbar,
                "block_w": block_w, "block_h": block_h,
                "lh_c": lh_c, "lh_t": lh_t, "lh_s": lh_s,
                "flag_w": flag_w, "flag_h": flag_h, "fgap": fgap,
                "fc": f_country, "ft": f_time, "fs": f_sub, "ctrl_r": ctrl_r, "s": s}

    # ---------------------------------------------------------------- render
    def redraw(self):
        transp = self._eff_transp()
        c = self.canvas
        c.delete("all")
        self.items = []
        self.buttons = []

        if self.view == "horarios":
            self._redraw_horarios(transp)
            return

        if self.cfg["size_mode"] == "fullscreen":
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            best = 1.0
            for cand in [x / 10.0 for x in range(8, 121)]:
                L = self.compute_layout(cand)
                if L["W"] <= sw * 0.95 and L["H"] <= sh * 0.95:
                    best = cand
                else:
                    break
            L = self.compute_layout(best)
            W, H = sw, sh
            ox = (sw - L["W"]) // 2
            oy = (sh - L["H"]) // 2
            self.root.geometry("%dx%d+0+0" % (sw, sh))
        else:
            L = self.compute_layout(self.cfg["scale"])
            W, H = L["W"], L["H"]
            ox = oy = 0
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            x, y = self._manual_pos(W, H, sw, sh)
            self.root.geometry("%dx%d+%d+%d" % (W, H, x, y))

        c.config(width=W, height=H)
        self.cw, self.ch = W, H
        tc = self.text_colors()

        # ---- fondo ----
        if transp:
            c.configure(bg=TKEY)
            self.root.configure(bg=TKEY)
        else:
            g1, g2 = self.bg_colors()
            c.configure(bg=g1)
            steps = max(1, int(H))
            for i in range(steps):
                c.create_line(0, i, W, i, fill=interp(g1, g2, i / steps))

        # ---- bloques ----
        s = L["s"]
        sh_dx = max(1, int(2 * s))
        horiz = self.cfg["orientation"] == "horizontal"
        for i, (country, city, tz, off) in enumerate(CITIES):
            if horiz:
                bx = ox + L["pad"] + i * (L["block_w"] + L["gap"])
                by = oy + L["topbar"]
            else:
                bx = ox + L["pad"]
                by = oy + L["topbar"] + i * (L["block_h"] + L["gap"])

            # bandera + pais
            tx = bx
            if self.cfg["show_flags"]:
                self._draw_flag(bx, by + max(0, (L["lh_c"] - L["flag_h"]) // 2),
                                L["flag_w"], L["flag_h"], country)
                tx = bx + L["flag_w"] + L["fgap"]
            c.create_text(tx, by, anchor="nw", text=country.upper(),
                          fill=tc["accent"], font=L["fc"])

            ty = by + L["lh_c"] + int(2 * s)
            sh = c.create_text(bx + sh_dx, ty + sh_dx, anchor="nw", text="",
                               fill=tc["shadow"], font=L["ft"])
            tm = c.create_text(bx, ty, anchor="nw", text="",
                               fill=tc["time"], font=L["ft"])
            sy = ty + L["lh_t"] + int(2 * s)
            sb = c.create_text(bx, sy, anchor="nw", text="",
                               fill=tc["city"], font=L["fs"])
            self.items.append({"time": tm, "shadow": sh, "sub": sb,
                               "tz": tz, "off": off, "city": city})

        # ---- botones arriba a la derecha ----
        r = L["ctrl_r"]
        cy = oy + L["topbar"] // 2
        gapb = int(r * 2 + 8 * s)
        x = ox + W - L["pad"] - r if self.cfg["size_mode"] != "fullscreen" else W - r - int(20 * s)
        for name in ("settings", "full", "compact", "horarios"):
            self._draw_button(x, cy, r, name, tc)
            self.buttons.append((x, cy, r + 4, name))
            x -= gapb

        # ---- grip de redimension (solo modo manual y flotante) ----
        if self.cfg["size_mode"] != "fullscreen" and not self._anchored():
            gx = ox + W - int(3 * s)
            gy = oy + H - int(3 * s)
            g = int(14 * s)
            c.create_polygon(gx - g, gy, gx, gy, gx, gy - g, fill=tc["sub"], outline="")

        self._update_time()
        self._pin_bottom()

    # ==================================================== VISTA HORARIOS
    def compute_layout_horarios(self, s):
        f_country = self.make_font(max(8, int(11 * s)), "country")
        f_phase = self.make_font(max(12, int(17 * s)), "time")
        f_msg = self.make_font(max(8, int(10 * s)), "sub")
        lh_c = f_country.metrics("linespace")
        lh_p = f_phase.metrics("linespace")
        lh_m = f_msg.metrics("linespace")

        flag_h = lh_c if self.cfg["show_flags"] else 0
        flag_w = int(flag_h * 1.5) if self.cfg["show_flags"] else 0
        fgap = int(6 * s) if self.cfg["show_flags"] else 0
        bar_h = max(6, int(9 * s))
        ebar_h = max(4, int(6 * s))
        # temporizador de Elias en monoespaciada (digitos de ancho fijo,
        # asi el contador no "baila" cada segundo)
        f_elias = tkfont.Font(family="Consolas", size=max(11, int(14 * s)))
        lh_ev = f_elias.metrics("linespace")

        sample_ph = "\U0001F37D\uFE0F Hora de comer   12:00"
        # el consejo mas largo de PHASES + ciudad + fecha, para reservar ancho
        sample_ms = "En casa, a punto de dormir: mejor esperar a ma\u00F1ana . Santiago . Xxx 00 Xxx"
        block_w = 0
        for country, city, tz, off in CITIES:
            cw = flag_w + fgap + f_country.measure(country.upper())
            block_w = max(block_w, cw, f_phase.measure(sample_ph),
                          f_msg.measure(sample_ms))
        # un poco mas de ancho para que los mensajes nuevos respiren
        block_w += int(14 * s)

        pad = int(14 * s)
        gap = int(12 * s)
        ctrl_r = max(8, int(9 * s))
        topbar = ctrl_r * 2 + int(10 * s)
        base = lh_c + lh_p + lh_m + bar_h + int(10 * s)
        # bloque extra de Elias: etiqueta + temporizador + barra de progreso
        chile_extra = (int(10 * s) + lh_c + int(3 * s) + lh_ev
                       + int(8 * s) + ebar_h + int(6 * s))
        block_h = base
        block_h_chile = base + chile_extra

        min_w = int(ctrl_r * 2 * 4 + 40 * s)
        if self.cfg["orientation"] == "horizontal":
            bh = max(block_h, block_h_chile)
            cw = pad * 2 + block_w * len(CITIES) + gap * (len(CITIES) - 1)
            ch = topbar + bh + pad
        else:
            cw = pad * 2 + block_w
            ch = topbar + block_h * 2 + block_h_chile + gap * (len(CITIES) - 1) + pad
        cw = max(cw, min_w)

        return {"W": cw, "H": ch, "pad": pad, "gap": gap, "topbar": topbar,
                "block_w": block_w, "block_h": block_h, "block_h_chile": block_h_chile,
                "lh_c": lh_c, "lh_p": lh_p, "lh_m": lh_m,
                "bar_h": bar_h, "ebar_h": ebar_h, "lh_ev": lh_ev,
                "flag_w": flag_w, "flag_h": flag_h, "fgap": fgap,
                "fc": f_country, "fp": f_phase, "fm": f_msg, "fev": f_elias,
                "ctrl_r": ctrl_r, "s": s}

    def _redraw_horarios(self, transp):
        c = self.canvas
        if self.cfg["size_mode"] == "fullscreen":
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            best = 1.0
            for cand in [x / 10.0 for x in range(8, 121)]:
                L = self.compute_layout_horarios(cand)
                if L["W"] <= sw * 0.95 and L["H"] <= sh * 0.95:
                    best = cand
                else:
                    break
            L = self.compute_layout_horarios(best)
            W, H = sw, sh
            ox = (sw - L["W"]) // 2
            oy = (sh - L["H"]) // 2
            self.root.geometry("%dx%d+0+0" % (sw, sh))
        else:
            L = self.compute_layout_horarios(self.cfg["scale"])
            W, H = L["W"], L["H"]
            ox = oy = 0
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            x, y = self._manual_pos(W, H, sw, sh)
            self.root.geometry("%dx%d+%d+%d" % (W, H, x, y))

        c.config(width=W, height=H)
        self.cw, self.ch = W, H
        tc = self.text_colors()

        # ---- fondo ----
        if transp:
            c.configure(bg=TKEY)
            self.root.configure(bg=TKEY)
        else:
            g1, g2 = self.bg_colors()
            c.configure(bg=g1)
            steps = max(1, int(H))
            for i in range(steps):
                c.create_line(0, i, W, i, fill=interp(g1, g2, i / steps))

        # ---- bloques ----
        s = L["s"]
        horiz = self.cfg["orientation"] == "horizontal"
        bh_max = max(L["block_h"], L["block_h_chile"])
        oy_cursor = oy + L["topbar"]
        for i, (country, city, tz, off) in enumerate(CITIES):
            bhh = L["block_h_chile"] if country == "Chile" else L["block_h"]
            if horiz:
                bx = ox + L["pad"] + i * (L["block_w"] + L["gap"])
                by = oy + L["topbar"] + (bh_max - bhh) // 2
            else:
                bx = ox + L["pad"]
                by = oy_cursor
                oy_cursor += bhh + L["gap"]

            tx = bx
            if self.cfg["show_flags"]:
                self._draw_flag(bx, by + max(0, (L["lh_c"] - L["flag_h"]) // 2),
                                L["flag_w"], L["flag_h"], country)
                tx = bx + L["flag_w"] + L["fgap"]
            c.create_text(tx, by, anchor="nw", text=country.upper(),
                          fill=tc["accent"], font=L["fc"])

            ty = by + L["lh_c"] + int(2 * s)
            phase_id = c.create_text(bx, ty, anchor="nw", text="",
                                     fill=tc["time"], font=L["fp"])
            ty += L["lh_p"] + int(1 * s)
            msg_id = c.create_text(bx, ty, anchor="nw", text="",
                                   fill=tc["city"], font=L["fm"])
            ty += L["lh_m"] + int(2 * s)

            # barra de 24h con segmentos de fase
            bar_y = ty
            bar_h = L["bar_h"]
            for (p0, p1, _, _, _, _), col in zip(PHASES, PHASE_COLORS):
                x0 = bx + int(p0 / 24.0 * L["block_w"])
                x1 = bx + int(p1 / 24.0 * L["block_w"])
                c.create_rectangle(x0, bar_y, x1, bar_y + bar_h, fill=col, outline="")

            # marcador con halo (encima de la barra, animado en _update_horarios)
            glow = c.create_oval(0, 0, 0, 0, fill="#FFFFFF", outline="",
                                 stipple="gray25")
            marker = c.create_oval(0, 0, 0, 0, fill="#FFFFFF", outline="#FFFFFF")

            item = {"time": None, "shadow": None, "sub": None,
                    "tz": tz, "off": off, "city": city, "country": country,
                    "phase": phase_id, "msg": msg_id,
                    "marker": marker, "glow": glow,
                    "bar": (bx, bar_y, L["block_w"], bar_h),
                    "marker_r": max(4, int(bar_h * 0.6))}
            self.items.append(item)

            # bloque Elias (solo Chile) - tarjeta limpia con acento de color
            if country == "Chile":
                ey = bar_y + bar_h + int(10 * s)
                acc_w = max(2, int(3 * s))
                content_x = bx + acc_w + int(9 * s)
                # etiqueta (ELIAS . estado)
                t_id = c.create_text(content_x, ey, anchor="nw", text="",
                                     fill=tc["accent"], font=L["fc"])
                ey_v = ey + L["lh_c"] + int(3 * s)
                # temporizador en monoespaciada (no "baila")
                v_id = c.create_text(content_x, ey_v, anchor="nw", text="",
                                     fill=tc["time"], font=L["fev"])
                ey_b = ey_v + L["lh_ev"] + int(8 * s)
                eb_h = L["ebar_h"]
                bar_x1 = bx + L["block_w"]
                # barra de progreso: pista tenue + relleno (solo al trabajar)
                eb0 = c.create_rectangle(content_x, ey_b, bar_x1, ey_b + eb_h,
                                         fill="#FFFFFF", outline="", stipple="gray12",
                                         state="hidden")
                eb1 = c.create_rectangle(content_x, ey_b, content_x, ey_b + eb_h,
                                         fill="#4ade80", outline="", state="hidden")
                # acento vertical a la izquierda (color segun estado)
                accent = c.create_rectangle(bx, ey, bx + acc_w, ey_b + eb_h,
                                            fill="#4ade80", outline="")
                item["elias"] = {"t": t_id, "v": v_id, "eb0": eb0, "eb1": eb1,
                                 "accent": accent,
                                 "bar": (content_x, ey_b, bar_x1 - content_x, eb_h)}

        # ---- botones arriba a la derecha ----
        r = L["ctrl_r"]
        cy = oy + L["topbar"] // 2
        gapb = int(r * 2 + 8 * s)
        x = ox + W - L["pad"] - r if self.cfg["size_mode"] != "fullscreen" else W - r - int(20 * s)
        for name in ("settings", "full", "compact", "horarios"):
            self._draw_button(x, cy, r, name, tc)
            self.buttons.append((x, cy, r + 4, name))
            x -= gapb

        # ---- grip (solo modo manual y flotante) ----
        if self.cfg["size_mode"] != "fullscreen" and not self._anchored():
            gx = ox + W - int(3 * s)
            gy = oy + H - int(3 * s)
            g = int(14 * s)
            c.create_polygon(gx - g, gy, gx, gy, gx, gy - g, fill=tc["sub"], outline="")

        self._update_horarios()
        self._pin_bottom()

    def _phase_of(self, hour):
        for (p0, p1, emoji, name, msg, ok) in PHASES:
            if p0 <= hour < p1:
                return emoji, name, msg, ok
        p = PHASES[0]
        return p[2], p[3], p[4], p[5]

    def _elias_info(self):
        now, _ = self._now(ELIAS_TZ, ELIAS_OFF)
        tzinfo = now.tzinfo
        start = datetime(ELIAS_YEAR, ELIAS_MONTH, ELIAS_DAY, 0, 0, 0, tzinfo=tzinfo)
        if now < start:
            diff = start - now
            d, s = diff.days, int(diff.seconds)
            return ("count", "ELÍAS · empieza el 14 ago 2026",
                    "faltan %dd %02d:%02d:%02d" % (d, s // 3600, (s % 3600) // 60, s % 60), None)
        mins = now.hour * 60 + now.minute + now.second / 60.0
        ws, we = ELIAS_WORK
        if ws <= mins < we:
            frac = (mins - ws) / float(we - ws)
            left = we - mins
            return ("work", "ELÍAS · turno 09:00–18:30",
                    "quedan %02d:%02d" % (int(left // 60), int(left % 60)), frac)
        rem = (ws - mins) if mins < ws else (24 * 60 - mins + ws)
        return ("rest", "ELÍAS · descansando",
                "próximo turno en %02d:%02d" % (int(rem // 60), int(rem % 60)), None)

    def _update_horarios(self):
        c = self.canvas
        t0 = time.time()
        tc = self.text_colors()
        for it in self.items:
            dt, exact = self._now(it["tz"], it["off"])
            h24 = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
            emoji, name, msg, ok = self._phase_of(h24)
            tim = dt.strftime("%H:%M:%S") if self.cfg["show_seconds"] else dt.strftime("%H:%M")
            c.itemconfig(it["phase"], text="%s %s   %s" % (emoji, name, tim))
            extra = "  (aprox.)" if not exact else ""
            # el consejo se resalta: verde si conviene escribir, ambar si no
            c.itemconfig(it["msg"],
                         text="%s . %s . %s%s" % (msg, it["city"],
                                                  dt.strftime("%a %d %b"), extra),
                         fill=(ADVICE_OK if ok else ADVICE_NO))

            bx, by, bw, bh = it["bar"]
            frac = h24 / 24.0
            mx = bx + frac * bw
            my = by + bh / 2.0
            # color del marcador segun la fase (mismo color de la barra)
            pcol = "#FFFFFF"
            for (p0, p1, _, _, _, _), col in zip(PHASES, PHASE_COLORS):
                if p0 <= h24 < p1:
                    pcol = col
                    break
            breathe = math.sin(t0 * 4.2 + bx)
            mr = it["marker_r"] * (1.0 + 0.16 * breathe)
            gr = it["marker_r"] * (2.1 + 0.5 * breathe)      # halo mas amplio y suave
            c.coords(it["glow"], mx - gr, my - gr, mx + gr, my + gr)
            c.itemconfig(it["glow"], fill=pcol)
            c.coords(it["marker"], mx - mr, my - mr, mx + mr, my + mr)
            c.itemconfig(it["marker"], fill=interp(pcol, "#FFFFFF", 0.55))

            if "elias" in it:
                state, t1, t2, frac_e = self._elias_info()
                el = it["elias"]
                scol = {"work": ADVICE_OK, "rest": ADVICE_NO,
                        "count": "#7FC8FF"}.get(state, tc["accent"])
                c.itemconfig(el["t"], text=t1)
                c.itemconfig(el["v"], text=t2)
                c.itemconfig(el["accent"], fill=scol)
                ex, ey, ew, eh = el["bar"]
                if state == "work":
                    f = max(0.0, min(1.0, frac_e or 0.0))
                    c.itemconfig(el["eb0"], state="normal")
                    c.itemconfig(el["eb1"], state="normal", fill=scol)
                    c.coords(el["eb1"], ex, ey, ex + f * ew, ey + eh)
                else:
                    # sin barra "muerta" fuera del turno: se oculta pista y relleno
                    c.itemconfig(el["eb0"], state="hidden")
                    c.itemconfig(el["eb1"], state="hidden")

    def _toggle_view(self):
        self.view = "horarios" if self.view == "clock" else "clock"
        self.redraw()

    def _draw_button(self, cx, cy, r, name, tc):
        c = self.canvas
        d = tc["time"]
        sh = tc["shadow"]

        def line(a, b, x1, y1, x2, y2, col, w):
            c.create_line(cx + x1, cy + y1, cx + x2, cy + y2, fill=col,
                          width=w, capstyle="round")

        w = max(2, int(r * 0.28))
        for col, off in ((sh, 1), (d, 0)):
            if name == "settings":  # engranaje simplificado = 3 lineas
                for dy in (-r * 0.5, 0, r * 0.5):
                    c.create_line(cx - r * 0.7 + off, cy + dy + off,
                                  cx + r * 0.7 + off, cy + dy + off,
                                  fill=col, width=w, capstyle="round")
            elif name == "full":  # esquinas (pantalla completa)
                q = r * 0.8
                pts = [(-q, -q + r * 0.5, -q, -q, -q + r * 0.5, -q),
                       (q - r * 0.5, -q, q, -q, q, -q + r * 0.5),
                       (-q, q - r * 0.5, -q, q, -q + r * 0.5, q),
                       (q, q - r * 0.5, q, q, q - r * 0.5, q)]
                for x1, y1, x2, y2, x3, y3 in pts:
                    c.create_line(cx + x1 + off, cy + y1 + off, cx + x2 + off, cy + y2 + off,
                                  fill=col, width=w, capstyle="round")
                    c.create_line(cx + x2 + off, cy + y2 + off, cx + x3 + off, cy + y3 + off,
                                  fill=col, width=w, capstyle="round")
            elif name == "compact":  # cuadro pequeno
                q = r * 0.55
                c.create_rectangle(cx - q + off, cy - q + off, cx + q + off, cy + q + off,
                                   outline=col, width=w)
            elif name == "horarios":  # barras de horario (timeline)
                q = r * 0.78
                wb = max(2, q * 0.22)
                for k, hh in enumerate((0.42, 0.64, 0.86)):
                    x0 = cx - q + k * (q * 0.64)
                    y1 = cy + q * 0.8
                    y0 = cy + q * 0.8 - hh * q * 1.7
                    c.create_rectangle(x0 + off, y0 + off, x0 + wb + off, y1 + off,
                                       fill=col, outline="")

    # ------------------------------------------------------------- banderas
    def _draw_flag(self, x, y, w, h, country):
        c = self.canvas
        c.create_rectangle(x, y, x + w, y + h, outline="#333333", width=1)
        if country == "Venezuela":
            b = h / 3.0
            c.create_rectangle(x, y, x + w, y + b, fill="#FFCC00", outline="")
            c.create_rectangle(x, y + b, x + w, y + 2 * b, fill="#00247D", outline="")
            c.create_rectangle(x, y + 2 * b, x + w, y + h, fill="#CF142B", outline="")
            # estrellas (pequenos puntos blancos en la franja azul)
            for k in range(5):
                sx = x + w * (0.2 + 0.15 * k)
                sy = y + 1.5 * b
                c.create_oval(sx - 1, sy - 1, sx + 1, sy + 1, fill="#FFFFFF", outline="")
        elif country == "Chile":
            half = h / 2.0
            cant = w * 0.36
            c.create_rectangle(x + cant, y, x + w, y + half, fill="#FFFFFF", outline="")
            c.create_rectangle(x, y + half, x + w, y + h, fill="#D52B1E", outline="")
            c.create_rectangle(x, y, x + cant, y + half, fill="#0039A6", outline="")
            # estrella (punto blanco)
            sx, sy = x + cant / 2.0, y + half / 2.0
            rr = max(1.5, h * 0.12)
            c.create_oval(sx - rr, sy - rr, sx + rr, sy + rr, fill="#FFFFFF", outline="")
        else:  # Espana
            c.create_rectangle(x, y, x + w, y + h * 0.25, fill="#AA151B", outline="")
            c.create_rectangle(x, y + h * 0.25, x + w, y + h * 0.75, fill="#F1BF00", outline="")
            c.create_rectangle(x, y + h * 0.75, x + w, y + h, fill="#AA151B", outline="")

    # --------------------------------------------------------------- tiempo
    def _now(self, tz, off):
        if ZoneInfo is not None:
            try:
                return datetime.now(ZoneInfo(tz)), True
            except Exception:
                pass
        return datetime.now(timezone(timedelta(hours=off))), False

    def _update_time(self):
        use24 = self.cfg["hour24"]
        secs = self.cfg["show_seconds"]
        show_date = self.cfg["show_date"]
        fmt = ("%H:%M:%S" if secs else "%H:%M") if use24 else ("%I:%M:%S %p" if secs else "%I:%M %p")
        for it in self.items:
            dt, exact = self._now(it["tz"], it["off"])
            txt = dt.strftime(fmt)
            if not use24 and txt.startswith("0"):
                txt = txt[1:]
            self.canvas.itemconfig(it["time"], text=txt)
            self.canvas.itemconfig(it["shadow"], text=txt)
            sub = ("%s . %s" % (it["city"], dt.strftime("%a %d %b"))) if show_date else it["city"]
            if not exact:
                sub += "  (aprox.)"
            self.canvas.itemconfig(it["sub"], text=sub)

    def _tick(self):
        if self.view == "horarios":
            self._update_horarios()
        else:
            self._update_time()
        self._pin_bottom()
        self.root.after(250, self._tick)

    # ---------------------------------------------------- ventana / escritorio
    def _anchored(self):
        """True cuando esta anclado al escritorio o pegado al fondo de
        pantalla (no flotante, no pantalla completa, no lanzado con
        --front). En este modo queda fijo a la derecha, sin poder moverse
        y al fondo de todo."""
        return ((self.cfg["desktop_mode"] or self.cfg.get("glue_wallpaper"))
                and self.cfg["size_mode"] != "fullscreen"
                and not self.force_front)

    def _eff_transp(self):
        """Fondo transparente efectivo: si el usuario lo activo o si esta
        anclado al escritorio (ahi se ve 'vacio', solo el reloj)."""
        return (self.cfg["transparent_bg"] or self._anchored()) and IS_WIN

    def _manual_pos(self, W, H, sw, sh):
        """Posicion en modo manual. Anclado: fijo a la derecha, centrado en
        vertical. Flotante: la ultima posicion guardada por el usuario."""
        margin = 16
        if self._anchored():
            x = max(0, sw - W - margin)
            y = max(0, (sh - H) // 2)
            return x, y
        x = min(max(int(self.cfg["x"]), 0), max(0, sw - 40))
        y = min(max(int(self.cfg["y"]), 0), max(0, sh - 40))
        return x, y

    def _hwnd(self):
        try:
            gp = ctypes.windll.user32.GetParent(self.root.winfo_id())
            return gp or self.root.winfo_id()
        except Exception:
            return self.root.winfo_id()

    def _want_glue(self):
        """True si debe quedar pegado al fondo de pantalla (WorkerW)."""
        return (bool(self.cfg.get("glue_wallpaper"))
                and self.cfg["size_mode"] != "fullscreen"
                and not self.force_front)

    def _find_workerw(self):
        """Localiza el WorkerW del escritorio (la capa del wallpaper, tras
        los iconos). Devuelve ese hwnd o Progman como respaldo."""
        u = ctypes.windll.user32
        wp = ctypes.c_void_p
        u.FindWindowW.restype = wp
        u.FindWindowW.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p]
        u.FindWindowExW.restype = wp
        u.FindWindowExW.argtypes = [wp, wp, ctypes.c_wchar_p, ctypes.c_wchar_p]
        u.SendMessageTimeoutW.argtypes = [wp, ctypes.c_uint, wp, wp,
                                          ctypes.c_uint, ctypes.c_uint, ctypes.c_void_p]
        progman = u.FindWindowW("Progman", None)
        try:
            # pide a Progman que genere el WorkerW del wallpaper
            u.SendMessageTimeoutW(progman, 0x052C, None, None, 0, 1000, None)
        except Exception:
            pass
        found = wp(0)
        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wp, wp)

        def _cb(hwnd, lparam):
            if u.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None):
                ww = u.FindWindowExW(None, hwnd, "WorkerW", None)
                if ww:
                    found.value = ww
            return True

        try:
            u.EnumWindows.argtypes = [WNDENUMPROC, ctypes.c_void_p]
            u.EnumWindows(WNDENUMPROC(_cb), 0)
        except Exception:
            pass
        return found.value or progman

    def _apply_glue(self):
        """Pega/despega la ventana del fondo de pantalla segun la config."""
        if not IS_WIN:
            return
        u = ctypes.windll.user32
        wp = ctypes.c_void_p
        u.SetParent.restype = wp
        u.SetParent.argtypes = [wp, wp]
        try:
            hwnd = self._hwnd()
            if self._want_glue():
                target = self._find_workerw()
                if target:
                    u.SetParent(hwnd, target)
                    self._glued = True
            elif self._glued:
                u.SetParent(hwnd, None)   # vuelve a ser ventana normal
                self._glued = False
        except Exception:
            self._glued = False

    def _toggle_glue(self):
        self.cfg["glue_wallpaper"] = not bool(self.cfg.get("glue_wallpaper"))
        self.apply_window_mode()
        self.redraw()
        save_config(self.cfg)

    def apply_window_mode(self):
        fs = self.cfg["size_mode"] == "fullscreen"
        eff_desktop = self._anchored()
        try:
            if fs or self.force_front:
                top = True
            elif eff_desktop:
                top = not self._settled     # visible al inicio, luego al fondo
            else:
                top = self.cfg["always_on_top"]
            self.root.attributes("-topmost", top)
        except Exception:
            pass
        try:
            self.root.attributes("-toolwindow", True)
        except Exception:
            pass
        try:
            if self._eff_transp():
                self.root.attributes("-transparentcolor", TKEY)
            else:
                self.root.attributes("-transparentcolor", "")
        except Exception:
            pass
        if IS_WIN:
            try:
                hwnd = self._hwnd()
                GWL_EXSTYLE = -20
                WS_EX_NOACTIVATE = 0x08000000
                WS_EX_TOOLWINDOW = 0x00000080
                ex = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
                if eff_desktop:
                    ex |= WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW
                else:
                    ex &= ~WS_EX_NOACTIVATE
                ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, ex)
            except Exception:
                pass
        self._apply_glue()
        self._pin_bottom()

    def _settle(self):
        self._settled = True
        self.apply_window_mode()

    def _pin_bottom(self):
        # si esta pegado al wallpaper (WorkerW) no hace falta empujarlo al
        # fondo: ya vive por debajo de todas las ventanas
        if self._glued:
            return
        eff = self._anchored() and self._settled
        if not (IS_WIN and eff):
            return
        try:
            hwnd = self._hwnd()
            ctypes.windll.user32.SetWindowPos(hwnd, 1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)
        except Exception:
            pass

    # --------------------------------------------------------- interacciones
    def _hit_button(self, x, y):
        for cx, cy, r, name in self.buttons:
            if abs(x - cx) <= r and abs(y - cy) <= r:
                return name
        return None

    def _press(self, e):
        name = self._hit_button(e.x, e.y)
        if name == "settings":
            self.open_settings(); self._mode = None; return
        if name == "full":
            self._toggle_fullscreen(); self._mode = None; return
        if name == "compact":
            self._set_compact(); self._mode = None; return
        if name == "horarios":
            self._toggle_view(); self._mode = None; return
        # Anclado al escritorio: queda FIJO (no se mueve ni se redimensiona).
        if self._anchored():
            self._mode = None
            return
        if self.cfg["size_mode"] != "fullscreen" and e.x >= self.cw - 18 and e.y >= self.ch - 18:
            self._mode = "resize"
            self._start = (e.x_root, e.y_root, self.cfg["scale"])
        elif self.cfg["size_mode"] != "fullscreen":
            self._mode = "move"
            self._start = (e.x_root - self.root.winfo_x(), e.y_root - self.root.winfo_y())
        else:
            self._mode = None

    def _motion(self, e):
        if self._mode == "move":
            self.root.geometry("+%d+%d" % (e.x_root - self._start[0], e.y_root - self._start[1]))
        elif self._mode == "resize":
            dx = e.x_root - self._start[0]
            dy = e.y_root - self._start[1]
            new = max(0.6, min(4.0, self._start[2] + (dx + dy) / 300.0))
            if abs(new - self.cfg["scale"]) >= 0.04:
                self.cfg["scale"] = round(new, 2)
                self.redraw()

    def _release(self, e):
        # No guardar posicion en anclado (queda fijo a la derecha); asi se
        # conserva la ultima posicion del modo flotante.
        if self.cfg["size_mode"] != "fullscreen" and not self._anchored():
            self.cfg["x"] = self.root.winfo_x()
            self.cfg["y"] = self.root.winfo_y()
        self._mode = None
        save_config(self.cfg)
        self._pin_bottom()

    # -------------------------------------------------------------- tamanos
    def _toggle_fullscreen(self):
        if self.cfg["size_mode"] == "fullscreen":
            self._exit_fullscreen()
        else:
            self._prev = (self.cfg["scale"], self.cfg["x"], self.cfg["y"])
            self.cfg["size_mode"] = "fullscreen"
            self.apply_window_mode()
            self.redraw()
            save_config(self.cfg)

    def _exit_fullscreen(self):
        if self.cfg["size_mode"] != "fullscreen":
            return
        self.cfg["size_mode"] = "manual"
        if self._prev:
            self.cfg["scale"], self.cfg["x"], self.cfg["y"] = self._prev
        self.apply_window_mode()
        self.redraw()
        save_config(self.cfg)

    def _set_compact(self):
        self.cfg["size_mode"] = "manual"
        self.cfg["scale"] = 0.8
        self.apply_window_mode()
        self.redraw()
        save_config(self.cfg)

    # ----------------------------------------------------------------- menu
    def _build_menu(self):
        m = self.menu
        m.add_command(label="Ajustes...", command=self.open_settings)
        m.add_command(label="Pantalla completa", command=self._toggle_fullscreen)
        m.add_command(label="Tamano pequeno", command=self._set_compact)
        m.add_command(label="Ver horarios / Ver reloj", command=self._toggle_view)
        m.add_separator()
        m.add_command(label="Anclar al escritorio / Flotante", command=self._toggle_desktop)
        m.add_command(label="Fijar al fondo de pantalla / Quitar", command=self._toggle_glue)
        m.add_command(label="Salir", command=self.quit)

    def _popup(self, e):
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()

    def _toggle_desktop(self):
        self.cfg["desktop_mode"] = not self.cfg["desktop_mode"]
        self.apply_window_mode()
        save_config(self.cfg)

    # ============================================================== AJUSTES
    def open_settings(self):
        if self.settings and tk.Toplevel.winfo_exists(self.settings):
            self.settings.lift(); self.settings.focus_force(); return
        BG = "#1c1c1e"; FG = "#f2f2f7"; SUB = "#9a9aa2"; CARD = "#2c2c2e"; AC = "#0a84ff"
        w = tk.Toplevel(self.root)
        self.settings = w
        w.title("Tipo de letra y color")
        w.configure(bg=BG)
        w.attributes("-topmost", True)
        w.resizable(False, False)
        w.geometry("+%d+%d" % (self.root.winfo_x(), self.root.winfo_y() + 40))

        def header(t):
            tk.Label(w, text=t, bg=BG, fg=SUB, font=("Segoe UI", 9, "bold"),
                     anchor="w").pack(fill="x", padx=16, pady=(12, 2))

        tk.Label(w, text="Tipo de letra y color", bg=BG, fg=FG,
                 font=("Segoe UI Semibold", 13)).pack(pady=(14, 2))

        # ---------- Fuente ----------
        header("TIPO DE LETRA")
        frow = tk.Frame(w, bg=BG); frow.pack(fill="x", padx=12)
        self._font_btns = {}

        def choose_font(fam):
            self.cfg["font"] = fam
            for f, lb in self._font_btns.items():
                lb.configure(highlightbackground=(AC if f == fam else CARD),
                             highlightcolor=(AC if f == fam else CARD))
            self.redraw(); save_config(self.cfg)

        for fam in FONTS:
            lb = tk.Label(frow, text="12", bg=CARD, fg=FG, width=3, height=1,
                          font=(fam, 15), highlightthickness=2,
                          highlightbackground=(AC if fam == self.cfg["font"] else CARD))
            lb.pack(side="left", padx=3, pady=2)
            lb.bind("<Button-1>", lambda e, f=fam: choose_font(f))
            self._font_btns[fam] = lb

        # ---------- Grosor ----------
        header("GROSOR DE LA LETRA  (fina  <->  gruesa)")
        gv = tk.IntVar(value=int(self.cfg["weight"]))

        def on_weight(_=None):
            self.cfg["weight"] = gv.get()
            self.redraw(); save_config(self.cfg)

        tk.Scale(w, from_=0, to=3, orient="horizontal", variable=gv, showvalue=False,
                 command=on_weight, bg=BG, fg=FG, troughcolor=CARD, highlightthickness=0,
                 length=300).pack(fill="x", padx=14)

        # ---------- Color del texto ----------
        header("COLOR DEL TEXTO  (arrastra sobre el arcoiris)")
        HB_W, HB_H = 300, 26
        hb = tk.Canvas(w, width=HB_W, height=HB_H, highlightthickness=0, bg=BG)
        hb.pack(padx=14, pady=(0, 2))
        for xx in range(HB_W):
            hb.create_line(xx, 0, xx, HB_H, fill=hsv_hex(xx / HB_W * 360, 1, 1))
        self._hue_marker = hb.create_rectangle(0, 0, 4, HB_H, outline="#ffffff", width=2)

        def set_hue_x(px):
            px = max(0, min(HB_W, px))
            self.cfg["txt_hue"] = px / HB_W * 360
            if self.cfg["txt_sat"] < 0.15:
                self.cfg["txt_sat"] = 1.0
                sv.set(100)
            hb.coords(self._hue_marker, px - 2, 0, px + 2, HB_H)
            self.redraw(); save_config(self.cfg)

        hb.bind("<Button-1>", lambda e: set_hue_x(e.x))
        hb.bind("<B1-Motion>", lambda e: set_hue_x(e.x))
        hb.coords(self._hue_marker,
                  self.cfg["txt_hue"] / 360 * HB_W - 2, 0,
                  self.cfg["txt_hue"] / 360 * HB_W + 2, HB_H)

        # intensidad (saturacion)
        header("INTENSIDAD DEL COLOR")
        sv = tk.IntVar(value=int(self.cfg["txt_sat"] * 100))

        def on_sat(_=None):
            self.cfg["txt_sat"] = sv.get() / 100.0
            self.redraw(); save_config(self.cfg)

        tk.Scale(w, from_=0, to=100, orient="horizontal", variable=sv, showvalue=False,
                 command=on_sat, bg=BG, fg=FG, troughcolor=CARD, highlightthickness=0,
                 length=300).pack(fill="x", padx=14)

        # brillo
        header("BRILLO DEL TEXTO")
        bv = tk.IntVar(value=int(self.cfg["txt_val"] * 100))

        def on_val(_=None):
            self.cfg["txt_val"] = max(0.1, bv.get() / 100.0)
            self.redraw(); save_config(self.cfg)

        tk.Scale(w, from_=10, to=100, orient="horizontal", variable=bv, showvalue=False,
                 command=on_val, bg=BG, fg=FG, troughcolor=CARD, highlightthickness=0,
                 length=300).pack(fill="x", padx=14)

        # swatches rapidos
        srow = tk.Frame(w, bg=BG); srow.pack(fill="x", padx=12, pady=(4, 2))

        def pick_sw(hexc):
            h, s, v = hex_to_hsv(hexc)
            self.cfg["txt_hue"] = h
            self.cfg["txt_sat"] = s
            self.cfg["txt_val"] = v
            sv.set(int(s * 100)); bv.set(int(v * 100))
            hb.coords(self._hue_marker, h / 360 * HB_W - 2, 0, h / 360 * HB_W + 2, HB_H)
            self.redraw(); save_config(self.cfg)

        for hx in SWATCHES:
            sw_c = tk.Canvas(srow, width=20, height=20, highlightthickness=1,
                             highlightbackground="#555", bg=hx)
            sw_c.pack(side="left", padx=2)
            sw_c.bind("<Button-1>", lambda e, h=hx: pick_sw(h))

        # ---------- Fondo ----------
        header("FONDO")
        brow = tk.Frame(w, bg=BG); brow.pack(fill="x", padx=12)
        i = 0
        for name, (g1, g2) in BACKGROUNDS.items():
            bc = tk.Canvas(brow, width=30, height=20, highlightthickness=2,
                           highlightbackground=(AC if self.cfg["bg"] == name else CARD))
            for yy in range(20):
                bc.create_line(0, yy, 30, yy, fill=interp(g1, g2, yy / 20))
            bc.grid(row=i // 7, column=i % 7, padx=3, pady=3)
            bc.bind("<Button-1>", lambda e, n=name: self._set_bg(n))
            i += 1

        tvar = tk.BooleanVar(value=self.cfg["transparent_bg"])

        def on_transp():
            self.cfg["transparent_bg"] = tvar.get()
            self.apply_window_mode(); self.redraw(); save_config(self.cfg)

        tk.Checkbutton(w, text="Fondo transparente (solo el texto sobre el wallpaper)",
                       variable=tvar, command=on_transp, bg=BG, fg=FG, selectcolor=CARD,
                       activebackground=BG, activeforeground=FG,
                       font=("Segoe UI", 9)).pack(anchor="w", padx=14, pady=(6, 0))

        # ---------- Opciones ----------
        header("OPCIONES")
        opts = tk.Frame(w, bg=BG); opts.pack(fill="x", padx=14)

        def mk_check(text, key, extra=None):
            var = tk.BooleanVar(value=self.cfg[key])

            def cb():
                self.cfg[key] = var.get()
                if extra:
                    extra()
                self.redraw(); save_config(self.cfg)
            tk.Checkbutton(opts, text=text, variable=var, command=cb, bg=BG, fg=FG,
                           selectcolor=CARD, activebackground=BG, activeforeground=FG,
                           font=("Segoe UI", 9)).pack(anchor="w")

        mk_check("Mostrar banderas", "show_flags")
        mk_check("Mostrar segundos", "show_seconds")
        mk_check("Mostrar fecha", "show_date")
        mk_check("Formato 24 horas", "hour24")
        mk_check("Anclado al escritorio (no emergente)", "desktop_mode", extra=self.apply_window_mode)
        mk_check("Fijar al fondo de pantalla (queda tras todo)", "glue_wallpaper", extra=self.apply_window_mode)
        mk_check("Siempre encima (modo flotante)", "always_on_top", extra=self.apply_window_mode)

        # orientacion + tamano
        row2 = tk.Frame(w, bg=BG); row2.pack(fill="x", padx=12, pady=(6, 2))

        def set_orient(o):
            self.cfg["orientation"] = o; self.redraw(); save_config(self.cfg)

        def set_scale(v):
            self.cfg["size_mode"] = "manual"; self.cfg["scale"] = v
            self.apply_window_mode(); self.redraw(); save_config(self.cfg)

        def btn(parent, text, cmd):
            b = tk.Button(parent, text=text, command=cmd, bg=CARD, fg=FG, bd=0,
                          activebackground=AC, activeforeground="#fff",
                          font=("Segoe UI", 9), padx=8, pady=4)
            b.pack(side="left", padx=3)
            return b

        header("ORIENTACION Y TAMANO")
        r1 = tk.Frame(w, bg=BG); r1.pack(fill="x", padx=12)
        btn(r1, "Vertical", lambda: set_orient("vertical"))
        btn(r1, "Horizontal", lambda: set_orient("horizontal"))
        r3 = tk.Frame(w, bg=BG); r3.pack(fill="x", padx=12, pady=(4, 2))
        btn(r3, "Pequeno", lambda: set_scale(0.8))
        btn(r3, "Mediano", lambda: set_scale(1.0))
        btn(r3, "Grande", lambda: set_scale(1.4))
        btn(r3, "Pantalla completa", self._toggle_fullscreen)

        tk.Button(w, text="Cerrar", command=w.destroy, bg=AC, fg="#fff", bd=0,
                  font=("Segoe UI Semibold", 10), padx=12, pady=6).pack(pady=12)

    def _set_bg(self, name):
        self.cfg["bg"] = name
        self.redraw(); save_config(self.cfg)
        if self.settings and tk.Toplevel.winfo_exists(self.settings):
            self.settings.destroy(); self.open_settings()

    def quit(self):
        if self.cfg["size_mode"] != "fullscreen":
            self.cfg["x"] = self.root.winfo_x()
            self.cfg["y"] = self.root.winfo_y()
        save_config(self.cfg)
        self.root.destroy()


def _log_error():
    import traceback
    tb = traceback.format_exc()
    print(tb)  # visible en consola (diagnostico.bat)
    path = os.path.join(config_dir(), "error.log")
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write("Reloj Mundial - error al iniciar\n")
            f.write(datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
            f.write(tb)
    except Exception:
        pass
    return path, tb


def main():
    front = "--front" in sys.argv
    # --flotante: salida de emergencia. Al pegarse al fondo de pantalla el
    # widget deja de ser clickeable; este flag lo devuelve a modo flotante
    # (movible, con fondo) y desactiva el pegado antes de abrir.
    if "--flotante" in sys.argv:
        try:
            cfg = load_config()
            cfg["glue_wallpaper"] = False
            cfg["desktop_mode"] = False
            save_config(cfg)
        except Exception:
            pass
    try:
        root = tk.Tk()
        ClockWidget(root, front=front)
        root.mainloop()
    except Exception:
        path, tb = _log_error()
        try:
            err = tk.Tk()
            err.title("Reloj Mundial - error")
            err.attributes("-topmost", True)
            tk.Label(err, text="No se pudo iniciar el widget. Detalle:",
                     justify="left", padx=14, pady=(14, 4),
                     font=("Segoe UI", 10, "bold")).pack(anchor="w")
            txt = tk.Text(err, width=90, height=16, wrap="word",
                          font=("Consolas", 9))
            txt.insert("1.0", tb + "\n\nGuardado en: " + path)
            txt.configure(state="disabled")
            txt.pack(padx=14, pady=4, fill="both", expand=True)
            tk.Button(err, text="Cerrar", command=err.destroy,
                      padx=12, pady=6).pack(pady=(0, 14))
            err.mainloop()
        except Exception:
            pass


if __name__ == "__main__":
    main()
