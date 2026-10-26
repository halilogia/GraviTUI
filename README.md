# GraviTUI

Ratatui'den esinlenen, **sıfır pip bağımlılıklı**, 24-bit TrueColor destekli evrensel
Pure Python 3 TUI çerçevesi. Windows Terminal'de (VT100 + UTF-8) birinci sınıf çalışır.

- **Diff tabanlı çizim:** `DiffWriter` yalnızca değişen hücreleri imleç atlamalarıyla yazar (flicker-free, 60 FPS hedefi).
- **Ratatui tarzı layout:** `Layout.split(area, dir, [Percentage, Length, Ratio, Min, Max, Fill])`.
- **Widget seti:** Block, Paragraph (Span/Line, word wrap), ListWidget, TableWidget, Gauge, Tabs, Popup.
- **Süper güçler:** `Canvas3D` (yazılım rasterizer, z-buffer, flat shading), `ParticleFX` (parçacık, shake, glitch), `TileMap` (katmanlar + BFS), `Tree` (katlanabilir ağaç), `ProceduralFlower` (prosedürel zambak), `CyberEye` (karakter matrisli siber göz).
- **Entegre Uygulamalar (`apps/`):** RPG Dice Roller (3D zarlar), Office Manager Tycoon (ofis simülasyonu), Monopoly (40 kare + 100k simülasyon).

## 🚀 Hızlı Başlangıç & Merkezi Hub

Tüm uygulama ve örnekleri tek bir etkileşimli terminal menüsünden başlatmak için:

```powershell
python run_hub.py           # Etkileşimli TUI Launcher
python run_hub.py monopoly  # Doğrudan Monopoly başlatır
python run_hub.py dice      # Doğrudan RPG Dice başlatır
python run_hub.py office    # Doğrudan Office Manager başlatır
```

## 📋 Temel Örnekler & Uygulamalar

| # | Yol | Açıklama |
|---|-----|----------|
| 1 | `apps/rpg_dice/main.py` | 3D çokyüzlü RPG zarları (d4-d100), Euler rotasyonu, DC kontrolleri |
| 2 | `apps/office_manager/main.py` | 24-bit ofis haritası, çalışan durum makineleri ve ekonomi |
| 3 | `apps/monopoly/main.py` | Klasik Monopoly oyunu + 100.000 oyunluk Monte Carlo ısı haritası |
| 4 | `examples/05_procedural_flower.py` | 24-bit alt-piksel prosedürel zambak büyüme simülatörü |
| 5 | `examples/06_cyber_eye.py` | ASCII kod matrisi tabanlı siber göz ve otonom bakış takibi |
| 6 | `examples/02_3d_polyhedron.py` | Z-buffer yazılım rasterizer'ı ve 3D d20 dönme fiziği |
| 7 | `examples/03_dashboard.py` | Canlı telemetri panosu ve flexbox layout |

## Gereksinimler

Python 3.9+ (3.13 ile doğrulandı). Windows'ta `msvcrt`/`ctypes` (stdlib). Harici paket yok.
Ayrıntılar: [ARCHITECTURE.md](ARCHITECTURE.md), [ROADMAP.md](ROADMAP.md), [CHANGELOG.md](CHANGELOG.md).

## Lisans

GPL-3.0 — bkz. [LICENSE](LICENSE).
