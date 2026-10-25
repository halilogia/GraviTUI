# GraviTUI Mimarisi

## Katmanlar

```
gravitui/
  core/        terminal.py  buffer.py  diff.py  style.py   (saf motor, widget bilmez)
  layout/      rect.py  constraint.py  layout.py           (saf hesap, çıktı bilmez)
  widgets/     base.py block.py paragraph.py list_table.py gauge.py tabs.py modal.py
  extensions/  canvas3d.py particles.py tilemap.py tree.py (isteğe bağlı süper güçler)
  app.py       alt-screen + 60 FPS döngüsü (draw / on_key)
```

Bağımlılık yönü tek taraflıdır: `extensions -> widgets -> core/layout`. `layout` ve `core`
birbirinden yalnızca `Rect` üzerinden haberdardır; hiçbiri `widgets`'i içe aktarmaz.

## Çizim hattı

```
App.run
 ├─ Terminal.poll_key() ──► on_key(key)
 ├─ buf.clear(); draw(buf, dt)      # widget.render(area, buf)
 └─ DiffWriter.flush(buf)           # önceki kareyle fark -> tek write
```

1. Widget'lar yalnızca `Buffer`'a yazar (I/O yok → headless test edilebilir).
2. `DiffWriter.render(buf)` önceki `Buffer` kopyasıyla hücre hücre karşılaştırır.
3. Değişen hücreler soldan sağa; ardışıksa tek `\x1b[{y+1};{x+1}H` atlaması, stil değişmedikçe
   SGR tekrarlanmaz. İlk kare / boyut değişimi `\x1b[2J` ile tam çizilir.

## Temel tipler

| Tip | Not |
|-----|-----|
| `Color(r,g,b)` | donmuş, 0-255 kıstırılır; `from_hex`, `from_hsv`, `lerp`, `scale` |
| `Style(fg,bg,bold,dim,italic,underline)` | `patch()` ile bindirme, `sgr()` ile ANSI |
| `Cell(char,fg,bg,style)` | eşitlik karşılaştırması diff'in temelidir |
| `Buffer(w,h)` | `put_str`, `set_style`, `fill`, kırpma (`clip`) ve sınır güvenli |
| `Rect(x,y,w,h)` | `pad`, `intersect`, `contains`, `split_h/v`, `centered` |

## Layout çözücü

`_solve(total, constraints, spacing)`: (1) `Length/Percentage/Ratio` sabit boyut alır;
(2) taşarsa sondan kırpılır; (3) kalan alan `Min/Max/Fill` parçalarına ağırlıkla dağıtılır,
`Max` sınırına ulaşan parça doyar ve döngü kalanla tekrarlanır. Toplam asla `area`'yı aşmaz.

## Widget sözleşmesi

`Widget.render(area: Rect, buf: Buffer)` — `area` dışına yazmamalı (`clip=` kullan),
`area.is_empty()` durumunda sessizce dönmeli. `block=` alan widget'lar önce bloğu çizip
`block.inner(area)` içinde devam eder.

## Canvas3D

Yazılım rasterizer: model -> `Quaternion`/`Matrix4` döndürme -> kamera `z += distance` ->
yüz normali -> backface culling -> flat shading (`ambient + diffuse`) -> perspektif izdüşüm ->
barycentric üçgen dolgu + z-buffer. Hücre başına iki dikey piksel (`▀`, fg=üst, bg=alt).
Işık vektörü, kameraya bakan yüzlerin normali (-z) ile aynı yarım uzaya bakmalıdır.

## Terminal

`enable_windows_vt()` (`SetConsoleMode` ENABLE_VIRTUAL_TERMINAL_PROCESSING + UTF-8 code page),
alt-screen `\x1b[?1049h/l`, imleç `\x1b[?25l/h`, `msvcrt.kbhit/getwch` ile bloklamayan klavye;
`translate_key()` saf fonksiyondur ve testlidir. POSIX'te `select` ile geri dönüş vardır.

## Testler

`tests/` tamamen headless (gerçek terminal gerekmez). Örnekler de `tests/test_examples.py`
ile üç boyutta (80x24, 120x40, 10x4) duman testine girer.
