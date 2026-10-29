# Stardew Valley TUI

GraviTUI üzerinde 24-bit TrueColor çiftçilik oyunu. Sıfır bağımlılık (yalnızca stdlib).

```powershell
python run_hub.py stardew          # hub üzerinden
python apps/stardew_valley/main.py # doğrudan (en az 96x27 terminal)
```

## Kontroller
| Tuş | İşlev |
|-----|-------|
| Oklar / WASD | Hareket (baktığın hücre vurgulanır) |
| 1-9 | Hotbar seçimi |
| C / Boşluk | Alet kullan / ekle / hasat et / kutuya bırak |
| E / I | Envanter (Enter: taşı / yer değiştir) |
| P | Pierre'in Mağazası (Tab: al/sat, Enter: 1 adet, A: 5 al / yığını sat) |
| Y | Yatağa git, günü bitir |
| Esc / Q | Çıkış (menülerde kapat) |

## Günlük döngü
Çapa -> tohum ek -> sula -> uyu. Uyurken yalnızca **sulanmış** topraktaki ekinler 1 gün büyür, topraklar kurur, sevkiyat kutusu
tam fiyattan satılır (Pierre anında öder ama %80), enerji tamamen yenilenir. Mevsim değişince yetişmeyen ekinler solar.
Saat gerçek zamanda akar (1 oyun dakikası = 0.7 sn); 00:00'dan sonra uyarı, 02:00'de bayılma (enerji yalnızca yarıya döner).

## Mimari
`calendar` -> `crops` -> `farm` -> `fishing` -> `tools` -> `items` -> `player` -> `shipping` -> `town` -> `game` (koordinatör)
-> `renderer` + `overlays` -> `main`. Çizim yalnızca `Buffer`'a yapılır; emoji yerine tek genişlikli glifler kullanılır
(çift sütun emoji DiffWriter hizasını bozar). `main.py` kendi klasörünü `sys.path`'ten çıkarır, çünkü `calendar.py` stdlib'i gölgelerdi.
