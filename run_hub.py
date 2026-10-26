#!/usr/bin/env python3
"""GraviTUI Evrensel Uygulama ve Demo Merkezi (Hub Launcher).

Kullanim:
    python run_hub.py              -> Etkilesimli TUI Hub Arayuzu
    python run_hub.py dice         -> RPG Dice Roller uygulamasini dogrudan baslatir
    python run_hub.py office       -> Office Manager Tycoon uygulamasini dogrudan baslatir
    python run_hub.py monopoly     -> Monopoly uygulamasini dogrudan baslatir
    python run_hub.py flower       -> Prosedurel Zambak gosterimini baslatir
    python run_hub.py eye          -> Siber Goz (CyberEye) gosterimini baslatir
    python run_hub.py --list       -> Uygulama ve ornek listesini yazdirir
"""
import os
import subprocess
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# GraviTUI kok dizinini sys.path'e ekle
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from gravitui import (
    Buffer, Color, Style, Rect, Layout, Length, Percentage, Fill, VERTICAL, HORIZONTAL,
    Block, Paragraph, Line, Span, ROUNDED, DOUBLE, CENTER,
    Terminal, DiffWriter
)

ITEMS = [
    {
        "id": "dice",
        "num": "1",
        "category": "apps",
        "title": "🎲 RPG Dice Roller",
        "path": os.path.join(ROOT_DIR, "apps", "rpg_dice", "main.py"),
        "cwd": os.path.join(ROOT_DIR, "apps", "rpg_dice"),
        "desc": "3D cokyuzlu zarlar (d4-d100), Euler rotasyonu, DC/Zorluk kontrolleri ve kritik efektler."
    },
    {
        "id": "office",
        "num": "2",
        "category": "apps",
        "title": "🏢 Office Manager Tycoon",
        "path": os.path.join(ROOT_DIR, "apps", "office_manager", "main.py"),
        "cwd": os.path.join(ROOT_DIR, "apps", "office_manager"),
        "desc": "24-bit TrueColor ofis floor plani, calisan AI durum makineleri, krizler ve sirket ekonomisi."
    },
    {
        "id": "monopoly",
        "num": "3",
        "category": "apps",
        "title": "🎩 Monopoly & Monte Carlo",
        "path": os.path.join(ROOT_DIR, "apps", "monopoly", "main.py"),
        "cwd": os.path.join(ROOT_DIR, "apps", "monopoly"),
        "desc": "Klasik 40 kare Monopoly TUI oyunu ve 100.000 oyunluk Monte Carlo inis/ROI isi haritasi."
    },
    {
        "id": "flower",
        "num": "4",
        "category": "examples",
        "title": "🌸 Procedural Lily Flower",
        "path": os.path.join(ROOT_DIR, "examples", "05_procedural_flower.py"),
        "cwd": ROOT_DIR,
        "desc": "24-bit TrueColor alt-piksel procedürel zambak buyume yasam dongusu ve kutsal geometri."
    },
    {
        "id": "eye",
        "num": "5",
        "category": "examples",
        "title": "👁️ CyberEye Matrix",
        "path": os.path.join(ROOT_DIR, "examples", "06_cyber_eye.py"),
        "cwd": ROOT_DIR,
        "desc": "ASCII karakter matrisi tabanli gozbebegi, dinamik goz kirpma ve otonom saccade bakis motoru."
    },
    {
        "id": "3d",
        "num": "6",
        "category": "examples",
        "title": "💠 3D Polyhedrons Demo",
        "path": os.path.join(ROOT_DIR, "examples", "02_3d_polyhedron.py"),
        "cwd": ROOT_DIR,
        "desc": "Pure Python Z-buffer yazilim rasterizer'i, flat shading ve d20/d12/kup donme fizigi."
    },
    {
        "id": "dashboard",
        "num": "7",
        "category": "examples",
        "title": "📊 Universal Dashboard",
        "path": os.path.join(ROOT_DIR, "examples", "03_dashboard.py"),
        "cwd": ROOT_DIR,
        "desc": "Ratatui bilesenleri: flexbox layout, gauge gostergeleri, tablolar ve sistem durumu."
    }
]

COLOR_BG = Color(10, 8, 22)
COLOR_PANEL = Color(16, 14, 32)
COLOR_BORDER = Color(90, 80, 140)
COLOR_BORDER_SEL = Color(255, 200, 60)
COLOR_TEXT = Color(230, 230, 245)
COLOR_MUTED = Color(130, 125, 160)
COLOR_GOLD = Color(255, 215, 80)
COLOR_CYAN = Color(50, 230, 255)
COLOR_GREEN = Color(90, 240, 150)
COLOR_MAGENTA = Color(230, 90, 220)


def run_target(item):
    """Hedef uygulamayi mevcut terminalde calistirir ve bitince geri doner."""
    cmd = [sys.executable, item["path"]]
    print(f"\033[2J\033[H\033[?25hBaslatiliyor: {item['title']} ...\n")
    try:
        subprocess.run(cmd, cwd=item["cwd"])
    except Exception as e:
        print(f"\nHata olustu: {e}\nDevam etmek icin Enter'a basin...")
        input()


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1].lower().strip("-")
        if arg in ("list", "help", "h"):
            print("GraviTUI Uygulama ve Ornek Listesi:\n")
            for it in ITEMS:
                print(f"  [{it['num']}] {it['title']} ({it['id']})")
                print(f"      {it['desc']}\n")
            return

        for it in ITEMS:
            if arg in (it["id"], it["num"], it["title"].lower()):
                run_target(it)
                return
        print(f"Bilinmeyen uygulama: {sys.argv[1]}. Listeyi gormek icin: python run_hub.py --list")
        return

    term = Terminal()
    writer = DiffWriter(sys.stdout)
    selected_idx = 0
    buf = None

    with term:
        writer.invalidate()
        while True:
            w, h = term.size()
            if buf is None or (buf.width, buf.height) != (w, h):
                buf = Buffer(w, h)
                writer.invalidate()

            # Tus islemleri
            while (k := term.poll_key()) is not None:
                k_low = k.lower()
                if k_low in ("q", "esc", "ctrl+c"):
                    return
                elif k_low in ("up", "w"):
                    selected_idx = (selected_idx - 1) % len(ITEMS)
                elif k_low in ("down", "s"):
                    selected_idx = (selected_idx + 1) % len(ITEMS)
                elif k_low in ("enter", "space"):
                    # Terminali gecici olarak serbest birak ve uygulamayi calistir
                    term.disable_raw_mode()
                    run_target(ITEMS[selected_idx])
                    term.enable_raw_mode()
                    writer.invalidate()
                elif k_low in "1234567":
                    idx = int(k_low) - 1
                    if 0 <= idx < len(ITEMS):
                        selected_idx = idx
                        term.disable_raw_mode()
                        run_target(ITEMS[selected_idx])
                        term.enable_raw_mode()
                        writer.invalidate()

            buf.clear()

            # Ana yerlesim: Baslik, Govde (Liste + Detay), Alt Bilgi
            rows = Layout.split(buf.area, VERTICAL, [Length(4), Fill(), Length(3)])

            # 1. Baslik Alani
            header_block = Block(
                borders=DOUBLE,
                title="🪐 GraviTUI Uygulama ve Ekosistem Merkezi",
                border_style=Style(fg=COLOR_GOLD, bg=COLOR_PANEL),
                title_style=Style(fg=COLOR_GOLD, bg=COLOR_PANEL, bold=True)
            )
            header_block.render(rows[0], buf)
            inner_h = header_block.inner(rows[0])
            sub_title = "Ratatui Mimarili 24-Bit TrueColor Python Cercevesi — Birlesik Uygulama Monoreposu"
            Paragraph(sub_title, Style(fg=COLOR_CYAN, bg=COLOR_PANEL), align=CENTER).render(inner_h, buf)

            # 2. Govde: Sol Menu (60%), Sag Bilgi Paneli (40%)
            cols = Layout.split(rows[1], HORIZONTAL, [Percentage(58), Fill()])

            # Sol Menu
            menu_block = Block(
                borders=ROUNDED,
                title="📋 Uygulama & Demo Listesi",
                border_style=Style(fg=COLOR_BORDER, bg=COLOR_BG),
                title_style=Style(fg=COLOR_CYAN, bold=True)
            )
            menu_block.render(cols[0], buf)
            inner_menu = menu_block.inner(cols[0])

            # Liste elemanlarini ciz
            y = inner_menu.y
            for i, it in enumerate(ITEMS):
                if y >= inner_menu.y + inner_menu.h:
                    break
                is_sel = (i == selected_idx)
                prefix = "  ▶ " if is_sel else "    "
                tag = "[APP]" if it["category"] == "apps" else "[DEMO]"
                tag_fg = COLOR_GREEN if it["category"] == "apps" else COLOR_MAGENTA
                num_badge = f"[{it['num']}] "
                
                fg = COLOR_GOLD if is_sel else COLOR_TEXT
                bg = Color(35, 30, 60) if is_sel else COLOR_BG
                
                line = Line([
                    Span(prefix, Style(fg=COLOR_GOLD if is_sel else COLOR_MUTED, bg=bg, bold=is_sel)),
                    Span(num_badge, Style(fg=COLOR_CYAN, bg=bg, bold=True)),
                    Span(f"{tag} ", Style(fg=tag_fg, bg=bg, bold=True)),
                    Span(f"{it['title']:<26}", Style(fg=fg, bg=bg, bold=is_sel)),
                ])
                line.render(Rect(inner_menu.x, y, inner_menu.w, 1), buf)
                y += 1
                if i in (2,):  # Kategori ayraci
                    if y < inner_menu.y + inner_menu.h:
                        buf.set_string(inner_menu.x + 4, y, "─" * (inner_menu.w - 8), Style(fg=COLOR_BORDER, bg=COLOR_BG))
                        y += 1

            # Sag Bilgi & Detay Paneli
            sel_item = ITEMS[selected_idx]
            info_block = Block(
                borders=ROUNDED,
                title=f"🔍 Detay: {sel_item['title']}",
                border_style=Style(fg=COLOR_BORDER_SEL, bg=COLOR_BG),
                title_style=Style(fg=COLOR_GOLD, bold=True)
            )
            info_block.render(cols[1], buf)
            inner_info = info_block.inner(cols[1])

            info_lines = [
                Line([Span("Kategori: ", Style(fg=COLOR_MUTED)), 
                      Span("Uygulama (apps/)" if sel_item["category"] == "apps" else "Prosedurel Demo (examples/)", 
                           Style(fg=COLOR_GREEN if sel_item["category"] == "apps" else COLOR_MAGENTA, bold=True))]),
                Line([Span("Konum:    ", Style(fg=COLOR_MUTED)),
                      Span(os.path.relpath(sel_item["path"], ROOT_DIR), Style(fg=COLOR_CYAN))]),
                Line([]),
                Line([Span("Aciklama:", Style(fg=COLOR_GOLD, bold=True))]),
            ]
            
            # Aciklamayi satirlara bol
            words = sel_item["desc"].split()
            cur = ""
            for w in words:
                if len(cur) + len(w) + 1 <= inner_info.w - 2:
                    cur = f"{cur} {w}" if cur else w
                else:
                    info_lines.append(Line([Span(f"  {cur}", Style(fg=COLOR_TEXT))]))
                    cur = w
            if cur:
                info_lines.append(Line([Span(f"  {cur}", Style(fg=COLOR_TEXT))]))

            info_lines.append(Line([]))
            info_lines.append(Line([Span("Calistirmak icin: ", Style(fg=COLOR_MUTED)), Span("[ENTER]", Style(fg=COLOR_GOLD, bold=True))]))
            info_lines.append(Line([Span("CLI ile: ", Style(fg=COLOR_MUTED)), Span(f"python run_hub.py {sel_item['id']}", Style(fg=COLOR_CYAN))]))

            for row_idx, il in enumerate(info_lines):
                if inner_info.y + row_idx < inner_info.y + inner_info.h:
                    il.render(Rect(inner_info.x, inner_info.y + row_idx, inner_info.w, 1), buf)

            # 3. Alt Yardim Bar
            help_block = Block(
                borders=ROUNDED,
                border_style=Style(fg=COLOR_BORDER, bg=COLOR_PANEL)
            )
            help_block.render(rows[2], buf)
            inner_help = help_block.inner(rows[2])
            help_text = " [↑/↓/W/S] Menude Gezin   [ENTER/Bosluk] Calistir   [1-7] Hizli Baslat   [Q/Esc] Cikis"
            Paragraph(help_text, Style(fg=COLOR_TEXT, bg=COLOR_PANEL), align=CENTER).render(inner_help, buf)

            writer.flush(buf)
            time.sleep(0.03)


if __name__ == "__main__":
    main()
