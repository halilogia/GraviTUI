# GraviTUI

Ratatui'den esinlenen, **sıfır pip bağımlılıklı**, 24-bit TrueColor destekli evrensel
Pure Python 3 TUI çerçevesi. Windows Terminal'de (VT100 + UTF-8) birinci sınıf çalışır.

- **Diff tabanlı çizim:** `DiffWriter` yalnızca değişen hücreleri imleç atlamalarıyla yazar (flicker-free, 60 FPS hedefi).
- **Ratatui tarzı layout:** `Layout.split(area, dir, [Percentage, Length, Ratio, Min, Max, Fill])`.
- **Widget seti:** Block, Paragraph (Span/Line, word wrap), ListWidget, TableWidget, Gauge, Tabs, Popup.
- **Süper güçler:** `Canvas3D` (yazılım rasterizer, z-buffer, flat shading), `ParticleFX` (parçacık, shake, glitch), `TileMap` (katmanlar + BFS), `Tree` (katlanabilir ağaç), `ProceduralFlower` (prosedürel zambak: yaşam döngüsü, kutsal geometri, polen).

## Hızlı başlangıç

```python
from gravitui import App, Block, Gauge, Layout, Length, Min, Paragraph, ROUNDED, VERTICAL

def draw(buf, dt):
    top, bottom = Layout.split(buf.area, VERTICAL, [Min(3), Length(3)])
    Paragraph("Merhaba GraviTUI", block=Block(ROUNDED, "Hello")).render(top, buf)
    Gauge(0.6, block=Block(ROUNDED, "İlerleme")).render(bottom, buf)

App(draw, on_key=lambda k: k == "q").run()
```

## Çalıştırma

```powershell
.\run.ps1            # menü (1-4 örnek, t testler)
run.bat 2            # 3D d20 / küp sahnesi
python -m unittest discover -s tests -t .
```

| # | Örnek | Gösterir |
|---|-------|----------|
| 1 | `examples/01_hello_ratatui.py` | layout, blok, paragraf, gauge |
| 2 | `examples/02_3d_polyhedron.py` | dönen d20 + küp (Canvas3D) |
| 3 | `examples/03_dashboard.py` | canlı telemetri panosu |
| 4 | `examples/04_office_mini.py` | karo haritası, BFS, parçacıklar |
| 5 | `examples/05_procedural_flower.py` | prosedürel zambak, yarım blok + braille, 4 palet |

## Gereksinimler

Python 3.9+ (3.13 ile doğrulandı). Windows'ta `msvcrt`/`ctypes` (stdlib). Harici paket yok.
Ayrıntılar: [ARCHITECTURE.md](ARCHITECTURE.md), [ROADMAP.md](ROADMAP.md), [CHANGELOG.md](CHANGELOG.md).

## Lisans

GPL-3.0 — bkz. [LICENSE](LICENSE).
