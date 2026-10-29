"""Modal ekranlar: envanter [E/I], Pierre'in Mağazası [P], gece özeti, balıkçılık, uyku onayı."""
from __future__ import annotations

from gravitui import ROUNDED, Block, Buffer, Color, Rect, Style

from . import town
from .fishing import FishPhase
from .game import FISHING, INVENTORY, SHOP, SLEEP, SUMMARY
from .items import item_name, sell_price

BG = Color(22, 20, 36)
TEXT, MUTED, GOLD = Color(230, 230, 240), Color(130, 130, 155), Color(255, 215, 80)
GOOD, BAD, CYAN = Color(110, 235, 140), Color(255, 110, 100), Color(120, 220, 255)
SEL_BG = Color(64, 52, 96)
TRACK_H = 14


def _st(fg: Color, bg: Color = BG, bold: bool = False) -> Style:
    return Style(fg=fg, bg=bg, bold=bold)


def _panel(buf: Buffer, area: Rect, w: int, h: int, title: str, border: Color = CYAN) -> Rect:
    box = area.centered(w, h)
    Block(ROUNDED, title, border_style=_st(border), title_style=_st(GOLD, bold=True),
          style=Style(bg=BG)).render(box, buf)
    return Rect(box.x + 2, box.y + 1, box.w - 4, box.h - 2)


def _row(buf: Buffer, inner: Rect, y: int, text: str, fg: Color, selected: bool = False) -> None:
    bg = SEL_BG if selected else BG
    buf.put_str(inner.x, inner.y + y, text[: inner.w].ljust(inner.w), _st(fg, bg, selected))


def draw(buf: Buffer, game, area: Rect) -> None:
    {INVENTORY: _inventory, SHOP: _shop, SUMMARY: _summary,
     FISHING: _fishing, SLEEP: _sleep}.get(game.mode, lambda *_: None)(buf, game, area)


def _inventory(buf: Buffer, game, area: Rect) -> None:
    inner = _panel(buf, area, 56, 19, "Envanter  [E/I]")
    slots = game.player.inventory.slots
    for i, slot in enumerate(slots):
        mark = "►" if i == game.cursor else " "
        pick = "*" if game.pick == i else " "
        tag = f"{i + 1}" if i < 9 else "-"
        if slot:
            val = sell_price(slot.item_id)
            line = f"{mark}{pick}[{tag}] {item_name(slot.item_id):<20} x{slot.qty:<4} " + (f"{val}g" if val else "")
        else:
            line = f"{mark}{pick}[{tag}] (boş)"
        _row(buf, inner, i, line, TEXT if slot else MUTED, i == game.cursor)
    _row(buf, inner, 13, f"Boş slot: {game.player.inventory.free_slots}/12   [1-9] = hotbar", MUTED)
    _row(buf, inner, 15, "Yukarı/Aşağı: gez   Enter: taşı / yer değiştir   Esc: kapat", MUTED)


def _shop(buf: Buffer, game, area: Rect) -> None:
    season = game.calendar.season_name
    inner = _panel(buf, area, 62, 19, f"Pierre'in Mağazası  [{season}]")
    p, tab = game.player, game.shop_tab
    buf.put_str(inner.x, inner.y, " SATIN AL ", _st(BG, GOLD, True) if tab == 0 else _st(MUTED))
    buf.put_str(inner.x + 12, inner.y, " SAT ", _st(BG, GOLD, True) if tab == 1 else _st(MUTED))
    buf.put_str(inner.x + inner.w - 12, inner.y, f"{p.gold}g".rjust(12), _st(GOLD, bold=True))
    rows = game._shop_rows()
    if not rows:
        _row(buf, inner, 2, "Satılacak bir şey yok." if tab else "Bu mevsimde tohum yok.", MUTED)
    for i, r in enumerate(rows[:10]):
        sel = i == game.cursor
        if tab == 0:
            line = f"{'►' if sel else ' '} {r.seed_name:<24} {r.seed_price:>4}g  elde: {p.inventory.count(r.seed_item)}"
            line += f"  ({r.days_to_grow} gün)"
        else:
            _, item_id, qty = r
            line = f"{'►' if sel else ' '} {item_name(item_id):<24} x{qty:<4} {town.sell_value(item_id)}g/adet"
        _row(buf, inner, 2 + i, line, TEXT, sel)
    _row(buf, inner, 13, game.message[0] if game.msg_t > 0 else "", GOOD if game.message[1] else BAD)
    hint = "Enter: 1 al   A: 5 al" if tab == 0 else "Enter: 1 sat   A: yığını sat"
    _row(buf, inner, 15, f"{hint}   Tab: Al/Sat   Esc: çık", MUTED)


def _summary(buf: Buffer, game, area: Rect) -> None:
    s = game.summary
    if s is None:
        return
    lines = s.report.lines
    inner = _panel(buf, area, 60, min(area.h - 2, 12 + len(lines)), "Gece Özeti", GOLD)
    _row(buf, inner, 0, f"{s.date_before}  ->  {s.date_after}", GOLD)
    _row(buf, inner, 2, "Sevkiyat Kutusu:", CYAN)
    shown = lines[: max(1, inner.h - 9)]
    if not lines:
        _row(buf, inner, 3, "  (kutu boştu)", MUTED)
    for i, ln in enumerate(shown):
        _row(buf, inner, 3 + i, f"  {item_name(ln.item_id):<22} {ln.qty:>4} x {ln.unit:>3}g = {ln.total:>6}g", TEXT)
    y = 3 + max(1, len(shown))
    _row(buf, inner, y, f"Toplam gelir: +{s.report.total}g   Kasa: {game.player.gold}g", GOLD)
    _row(buf, inner, y + 1, f"Büyüyen ekin: {s.grown}   Hasada hazır: {s.ready}", GOOD)
    for j, ev in enumerate(s.events[:2]):
        _row(buf, inner, y + 2 + j, ev, BAD)
    _row(buf, inner, inner.h - 1, "[Enter] Yeni güne başla", MUTED)


def _sleep(buf: Buffer, game, area: Rect) -> None:
    inner = _panel(buf, area, 46, 7, "Yatağa git?")
    _row(buf, inner, 0, "Günü bitirip uyuyacaksın: ekinler büyür,", TEXT)
    _row(buf, inner, 1, "sevkiyat kutusu satılır, enerji yenilenir.", TEXT)
    _row(buf, inner, 3, "[Y/Enter] Uyu     [N/Esc] Vazgeç", GOLD)


def _fishing(buf: Buffer, game, area: Rect) -> None:
    fg = game.fishing
    if fg is None:
        return
    inner = _panel(buf, area, 44, TRACK_H + 7, "Balıkçılık")
    col = {FishPhase.BITE: BAD, FishPhase.CAUGHT: GOOD, FishPhase.LOST: BAD}.get(fg.phase, TEXT)
    _row(buf, inner, 0, fg.message, col)
    if fg.phase == FishPhase.REEL or fg.done:
        lo, hi = fg.bar_range
        for r in range(TRACK_H):
            frac = 1.0 - (r + 0.5) / TRACK_H          # üst = 1
            in_bar = lo <= frac <= hi
            buf.put_str(inner.x + 14, inner.y + 2 + r, "▐██▌" if in_bar else "▐  ▌",
                        _st(GOOD if in_bar else MUTED, Color(30, 60, 40) if in_bar else BG))
        fr = min(TRACK_H - 1, max(0, int((1.0 - fg.fish_pos) * TRACK_H)))
        buf.put_str(inner.x + 16, inner.y + 2 + fr, "◆", _st(Color(255, 190, 90), Color(30, 60, 40) if lo <= fg.fish_pos <= hi else BG, True))
        n = round(fg.progress * TRACK_H)
        for r in range(TRACK_H):
            filled = r >= TRACK_H - n
            buf.put_str(inner.x + 24, inner.y + 2 + r, "█" if filled else "░",
                        _st(GOOD if filled else MUTED))
        buf.put_str(inner.x + 22, inner.y + 1, "ilerleme", _st(MUTED))
    _row(buf, inner, TRACK_H + 3, "Boşluk: çubuğu yükselt / çek   Esc: bırak" if not fg.done else "[Boşluk] Devam", MUTED)
