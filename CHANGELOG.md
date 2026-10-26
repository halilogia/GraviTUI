# Changelog

[Keep a Changelog](https://keepachangelog.com/) biçimi, [SemVer](https://semver.org/).

## [Unreleased]

### Eklendi
- `extensions.eye`: `CyberEye` — karakter matrisinden prosedürel 3D siber göz: küre analitiği (`z=√(R²-x²-y²)`, eğrilik
  gölgelemesi), parabolik göz kapakları, yumuşak göz kırpma, bakışa bağlı iris/lif/gözbebeği (dilation) ve parlama noktası,
  saccade + mikro-titreme + nefes, "cyber" (harf/rakam/matematik sembolü) ve "density" glif stilleri, 4 TrueColor palet
  (`Amber / Kehribar`, `Siber Yeşil / Matrix`, `Kanlı Ay / Kızıl`, `Sayborg Mavisi`). Matematik `eye_math.py` içinde.
  Örnek 06 ve `tests/test_eye.py`.
- `extensions.flower`: `ProceduralFlower` — Filiz → Sap/Yaprak → Tomurcuk → Açılış → Tam Zambak yaşam döngüsü (FSM),
  gerilimli (`ease_out_back`) taç yaprak açılışı, nefes animasyonu, polen parçacıkları, kutsal geometri
  yörünge çemberleri (braille), 4 TrueColor palet (`Zambak`, `Siber Lotus`, `Altın Orkide`, `Ruh Zambağı`).
  Matematik/tuval yardımcıları `flower_math.py` içinde. Örnek 05 ve `tests/test_flower.py`.

## [0.1.0] - 2026-10-25

### Eklendi
- `core`: `Color` (hex/HSV/lerp), `gradient`, `Style`, `Cell`, `Buffer`, `DiffWriter`, `Terminal`
  (Windows VT100 + UTF-8, alt-screen, imleç, `msvcrt` klavye).
- `layout`: `Rect`, `Percentage/Length/Ratio/Min/Max/Fill`, `Layout.split` (margin + spacing).
- `widgets`: `Block` (ALL/ROUNDED/DOUBLE/NONE, başlık hizalama, padding), `Paragraph`
  (Span/Line, word wrap, hizalama, scroll), `ListWidget`, `TableWidget`, `Gauge`, `Tabs`, `Popup`.
- `extensions`: `Canvas3D` (Vector3, Matrix4, Quaternion, Mesh3D küp/d20/oktahedron, flat shading,
  z-buffer), `ParticleFX` (burst/storm, shake, glitch), `TileMap` (katman + BFS), `Tree`.
- `App`: 60 FPS döngü yardımcısı.
- Örnekler 01-04, 69 headless birim testi, `run.bat`, `run.ps1`.
- Core dokümanlar: README, ARCHITECTURE, ROADMAP, CHANGELOG, KNOWLEDGE, TASKS, AGENTS, LICENSE (GPL-3.0).
