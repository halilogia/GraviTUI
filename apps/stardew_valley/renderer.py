"""24-bit TrueColor çizim: harita, HUD, hotbar. Her hücre 2 sütun; yalnızca tek genişlikli glifler
kullanılır (emoji çift sütun kaplayıp DiffWriter hizasını bozar)."""
from __future__ import annotations

import math
from typing import Tuple

from gravitui import ROUNDED, Block, Buffer, Color, Rect, Style

from . import overlays
from .calendar import Season
from .crops import STAGE_NAMES, Stage
from .farm import FARM_H, FARM_W, HOUSE_RECT, Tile
from .items import item_name
from .tools import WATER_CAPACITY

CELL_W = 2
MAP_W, MAP_H = FARM_W * CELL_W + 2, FARM_H + 2
PANEL_W = 30
SCREEN_W, SCREEN_H = MAP_W + PANEL_W, MAP_H + 7

GRASS = {Season.SPRING: (72, 150, 74), Season.SUMMER: (50, 128, 58),
         Season.FALL: (140, 118, 58), Season.WINTER: (208, 220, 232)}
TILLED_BG, WATERED_BG = (124, 84, 52), (78, 54, 40)
TEXT, MUTED, GOLD = Color(230, 230, 240), Color(130, 130, 155), Color(255, 215, 80)
PANEL_BG, GOOD, BAD = Color(18, 18, 30), Color(110, 235, 140), Color(255, 110, 100)
ENERGY_FG = Color(90, 220, 110)
STAGE_GLYPH = {Stage.SEED: "· ", Stage.SPROUT: "ψ ", Stage.VEGETATIVE: "ΨΨ",
               Stage.BLOOM: "Ψ*", Stage.HARVESTABLE: "●●"}
ARROW = {"UP": "▲", "DOWN": "▼", "LEFT": "◄", "RIGHT": "►"}
Cells = Tuple[str, str, Tuple[int, int, int], Tuple[int, int, int]]


def _c(rgb, night: float = 0.0, lit: float = 0.0) -> Color:
    """RGB -> Color; gece mavi-karanlığa kaydırır, `lit` (0..1) hedef hücreyi aydınlatır."""
    col = Color(*rgb)
    if night:
        col = col.lerp(Color(14, 18, 52), 0.55 * night)
    return col.lerp(Color(255, 245, 160), lit) if lit else col


def _hash(x: int, y: int) -> int:
    return (x * 73856093 ^ y * 19349663) & 0xFFFF


def _tile_cells(game, x: int, y: int, t: float) -> Cells:
    farm, season = game.farm, game.calendar.season
    tile = farm.tile(x, y)
    g = GRASS[season]
    h = _hash(x, y)
    grass_fg = tuple(int(v * 0.8) for v in g)
    if tile == Tile.GRASS:
        return ('"' if h % 5 == 0 else "," if h % 5 == 1 else " "), " ", grass_fg, g
    if tile == Tile.WEED:
        return "\"", "'", (150, 220, 90), g
    if tile == Tile.ROCK:
        return "●", "▄", (175, 175, 185), g
    if tile == Tile.WOOD:
        return "◘", "■", (150, 98, 52), g
    if tile == Tile.POND:
        wave = math.sin(t * 2.0 + x * 0.9 + y * 0.6)
        return ("≈" if wave > 0 else "~"), ("~" if wave > 0 else "≈"), (120, 180, 245), (36, 84, 160)
    if tile == Tile.SHIPPING_BIN:
        return "▣", "▣", (255, 220, 120), (120, 78, 44)
    if tile == Tile.FARMHOUSE:
        hx, hy, _, _ = HOUSE_RECT
        dx, dy = x - hx, y - hy
        if dy == 0:
            return "▒", "▒", (110, 30, 30), (170, 58, 52)
        if dy == 1:
            win = dx in (1, 4)
            return ("▐", "▌", (120, 190, 235), (200, 170, 120)) if win else (" ", " ", (0, 0, 0), (200, 170, 120))
        if dx in (2, 3):
            return ("▐", "█", (70, 44, 24), (200, 170, 120)) if dx == 2 else ("█", "•", (70, 44, 24), (200, 170, 120))
        return " ", " ", (0, 0, 0), (186, 156, 108)
    soil = TILLED_BG if tile == Tile.TILLED else WATERED_BG
    crop = farm.crops.get((x, y))
    if crop is None:
        return ("≡" if tile == Tile.TILLED else "≈"), ("≡" if tile == Tile.TILLED else "≈"), \
            tuple(int(v * 0.8) for v in soil), soil
    glyph = STAGE_GLYPH[crop.stage]
    color = crop.definition.color if crop.stage == Stage.HARVESTABLE else (90, 200, 80)
    return glyph[0], glyph[1], color, soil


def draw_map(buf: Buffer, game, ox: int, oy: int, t: float) -> None:
    night = game.calendar.daylight
    block = Block(ROUNDED, f"{game.calendar.season_name} Çiftliği",
                  border_style=Style(fg=Color(120, 100, 70)), title_style=Style(fg=GOLD, bold=True))
    block.render(Rect(ox, oy, MAP_W, MAP_H), buf)
    tx, ty = game.player.facing_pos()
    for y in range(FARM_H):
        for x in range(FARM_W):
            c0, c1, fg, bg = _tile_cells(game, x, y, t)
            lit = 0.28 if (x, y) == (tx, ty) else 0.0
            st = Style(fg=_c(fg, night, lit), bg=_c(bg, night, lit),
                       bold=game.farm.crops.get((x, y)) is not None and c0 == "●")
            buf.put_str(ox + 1 + x * CELL_W, oy + 1 + y, c0 + c1, st)
    p = game.player
    pbg = _c(_tile_cells(game, p.x, p.y, t)[3], night)
    buf.put_str(ox + 1 + p.x * CELL_W, oy + 1 + p.y, "@" + ARROW[p.facing.name],
                Style(fg=Color(255, 225, 190), bg=pbg, bold=True))


def _bar(buf: Buffer, x: int, y: int, w: int, frac: float, fg: Color, bg: Color) -> None:
    n = round(max(0.0, min(1.0, frac)) * w)
    buf.put_str(x, y, "█" * n, Style(fg=fg, bg=PANEL_BG))
    buf.put_str(x + n, y, "░" * (w - n), Style(fg=bg, bg=PANEL_BG))


def draw_hud(buf: Buffer, game, ox: int, oy: int) -> None:
    cal, p = game.calendar, game.player
    area = Rect(ox, oy, PANEL_W, MAP_H)
    Block(ROUNDED, "Durum", border_style=Style(fg=Color(90, 80, 140)),
          title_style=Style(fg=Color(120, 220, 255), bold=True), style=Style(bg=PANEL_BG)).render(area, buf)
    x, y, w = ox + 2, oy + 1, PANEL_W - 4
    label, val = Style(fg=MUTED, bg=PANEL_BG), lambda c, b=False: Style(fg=c, bg=PANEL_BG, bold=b)
    buf.put_str(x, y, f"{cal.weekday}. {cal.date_str}", val(TEXT, True))
    late = cal.is_late
    buf.put_str(x, y + 1, f"Saat  {cal.clock_str}" + ("  GEÇ OLDU!" if late else ""), val(BAD if late else TEXT, late))
    buf.put_str(x, y + 2, f"Para  {p.gold:,}g".replace(",", "."), val(GOLD, True))
    buf.put_str(x, y + 4, f"Enerji {p.energy}/{p.max_energy}", label)
    _bar(buf, x, y + 5, w, p.energy / p.max_energy, ENERGY_FG if p.energy > 60 else BAD, Color(50, 60, 55))
    buf.put_str(x, y + 6, f"Su {p.water}/{WATER_CAPACITY}", label)
    _bar(buf, x, y + 7, w, p.water / WATER_CAPACITY, Color(90, 160, 255), Color(40, 50, 80))
    slot = p.selected_slot()
    buf.put_str(x, y + 9, "Aktif:", label)
    buf.put_str(x, y + 10, (f"{item_name(slot.item_id)}" + (f" x{slot.qty}" if slot.qty > 1 else "")) if slot else "(boş)",
                val(Color(255, 190, 120), True))
    fx, fy = p.facing_pos()
    buf.put_str(x, y + 12, "Karşında:", label)
    buf.put_str(x, y + 13, _facing_text(game, fx, fy)[:w], val(TEXT))
    buf.put_str(x, y + 15, "Kutudaki: ", label)
    buf.put_str(x + 10, y + 15, f"{game.bin.pending_value()}g", val(GOLD))
    ready = sum(1 for c in game.farm.crops.values() if c.harvestable)
    buf.put_str(x, y + 16, f"Ekin: {len(game.farm.crops)} (hasat: {ready})", label)


NAMES = {Tile.GRASS: "Çimen", Tile.TILLED: "İşlenmiş toprak", Tile.WATERED: "Sulanmış toprak",
         Tile.ROCK: "Taş", Tile.WOOD: "Kütük", Tile.WEED: "Yabani ot", Tile.POND: "Gölet",
         Tile.FARMHOUSE: "Çiftlik evi", Tile.SHIPPING_BIN: "Sevkiyat kutusu"}


def _facing_text(game, x: int, y: int) -> str:
    if not game.farm.in_bounds(x, y):
        return "Harita sınırı"
    crop = game.farm.crops.get((x, y))
    if crop is not None:
        return f"{crop.definition.name}: {STAGE_NAMES[crop.stage]}"
    return NAMES[game.farm.tile(x, y)]


def draw_hotbar(buf: Buffer, game, ox: int, oy: int) -> None:
    p = game.player
    w = SCREEN_W // 9
    for i in range(9):
        slot = p.inventory.slots[i]
        sel = i == p.hotbar_index
        st = Style(fg=GOLD if sel else TEXT, bg=Color(60, 48, 24) if sel else PANEL_BG, bold=sel)
        name = item_name(slot.item_id)[: w - 3] if slot else "-"
        qty = f"x{slot.qty}" if slot and slot.qty > 1 else ""
        buf.put_str(ox + i * w, oy, f"{i + 1}".ljust(w), st)
        buf.put_str(ox + i * w, oy, f"{i + 1}:{name}", st)
        buf.put_str(ox + i * w, oy + 1, f" {qty}".ljust(w), st)


def draw_message(buf: Buffer, game, ox: int, oy: int) -> None:
    text, ok = game.message
    if game.msg_t > 0:
        buf.put_str(ox, oy, " " + text, Style(fg=GOOD if ok else BAD, bold=True))
    help_txt = " Hareket:WASD/Oklar  Kullan:C/Boşluk  Hotbar:1-9  Envanter:E  Mağaza:P  Uyu:Y  Çıkış:Esc"
    buf.put_str(ox, oy + 1, help_txt[: SCREEN_W], Style(fg=MUTED))


def render(game, buf: Buffer, t: float) -> None:
    """Tüm sahneyi ekranın üst-ortasına çizer; modal ekranlar `overlays` modülünde."""
    ox = max(0, (buf.width - SCREEN_W) // 2)
    draw_map(buf, game, ox, 0, t)
    draw_hud(buf, game, ox + MAP_W, 0)
    draw_hotbar(buf, game, ox, MAP_H)
    draw_message(buf, game, ox, MAP_H + 3)
    overlays.draw(buf, game, Rect(ox, 0, SCREEN_W, SCREEN_H))
