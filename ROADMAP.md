# Yol Haritası

## v0.1.0 — Temel (tamamlandı)
- [x] core: Color/Style, Cell/Buffer, DiffWriter, Terminal (Windows VT + msvcrt)
- [x] layout: Rect, Constraint, Layout.split
- [x] widgets: Block, Paragraph, List, Table, Gauge, Tabs, Popup
- [x] extensions: Canvas3D, ParticleFX, TileMap, Tree
- [x] 4 örnek, headless testler, `run.bat` / `run.ps1`

## v0.2.0 — Etkileşim
- [ ] Fare desteği (SGR 1006) ve odak/olay yönlendirme
- [ ] Yeniden boyutlandırma olayı (poll yerine `WINDOW_BUFFER_SIZE_EVENT`)
- [ ] Metin girişi widget'ı (TextInput) ve Scrollbar
- [ ] Geniş karakter (CJK / emoji) genişlik hesabı (`wcwidth` benzeri, stdlib ile)

## v0.3.0 — Görsel
- [ ] Canvas3D: Gouraud shading, doku/UV, çizgi (wireframe) modu, OBJ yükleyici
- [ ] Sparkline, BarChart, LineChart (braille alt-piksel canvas)
- [ ] Animasyon/tween yardımcıları ve tema sistemi

## v0.4.0 — Paketleme
- [ ] `pyproject.toml`, PyPI yayını (bağımlılıksız)
- [ ] Linux/macOS terminal modu (termios raw) için tam test
- [ ] Performans: yalnızca kirli satır takibi, ağır döngülerde `array`/bytearray tamponları

## Fikirler (kapsam dışı değil)
- Widget'lar için `StatefulWidget` ayrımı (Ratatui paritesi)
- Kaydet/oynat: karelerin `.ansi` dosyasına kaydı (devlog klipleri için)
