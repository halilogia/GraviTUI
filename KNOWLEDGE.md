# Bilgi Tabanı (Dersler ve Tuzaklar)

## Windows terminal
- ANSI için `SetConsoleMode(handle, mode | 0x0004)` (ENABLE_VIRTUAL_TERMINAL_PROCESSING) gerekir;
  Windows Terminal'de zaten açıktır, eski `conhost`'ta değildir.
- UTF-8 için `SetConsoleOutputCP(65001)` + `sys.stdout.reconfigure(encoding="utf-8")`.
- `msvcrt.getwch()` özel tuşlarda iki çağrı döner: önek `\x00`/`\xe0` + kod (`H`=yukarı, `P`=aşağı...).
- Alt-screen: `\x1b[?1049h`; çıkışta MUTLAKA `\x1b[?1049l` + imleci geri aç (`App` `finally` ile yapar).

## Diff motoru
- Aynı satırda ardışık değişen hücreler tek imleç atlamasıyla yazılır; atlama yalnızca
  `(cx, cy)` tahmini beklenen konumdan farklıysa eklenir.
- Stil değişmedikçe SGR yeniden yazılmaz; her SGR `0` ile başlar (sızıntı olmaz).
- İlk karede boş hücreler `\x1b[2J` ile temizlendiği için atlanır.

## Layout
- Tam sayı bölmede kalan piksel son esnek parçaya verilir; böylece toplam daima alana eşittir.
- `Min(n)` kalan alanı alır, `Max(n)` doyunca kalan diğer esnek parçalara akar.

## Canvas3D
- Kamera orijinde, +z'ye bakar; kameraya dönük yüz normali -z bileşenlidir. Işık vektörü
  (-z yönlü) bu yüzden `(-0.4, 0.7, -1)`; +z verilirse tüm yüzler yalnızca ambient alır.
- Mesh yüzleri dışa bakan CCW sırada olmalı (testler normalin merkezden dışa baktığını doğrular).
- Terminal hücresi ~1:2 olduğundan `▀` ile iki dikey piksel kullanmak kare piksel verir.

## Araçlar
- Git Bash'te Türkçe/tırnaklı çok satırlı heredoc bazen ayrıştırma hatası verir; dosyaları
  `Write` aracıyla yazmak güvenlidir.
- `run.bat` içinde `"%~dp0"` sonundaki `\` tırnağı kaçırır; `pushd "%~dp0"` kullanılır.
- Testler `python -m unittest discover -s tests -t .` ile çalışır (`-t .` paket köküdür).
