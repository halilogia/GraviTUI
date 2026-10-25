# AGENTS.md — GraviTUI için ajan kuralları

Genel kurallar kullanıcı düzeyindeki `AGENTS.md` / `CLAUDE.md` içindedir; burada yalnızca bu repoya özgü olanlar.

## Proje
Pure Python 3, **sıfır pip bağımlılığı** (yalnızca stdlib). Yeni bağımlılık eklenmez.
Windows Terminal birincil hedeftir; POSIX geri dönüşü korunur.

## Mimari kurallar
- Yön: `extensions -> widgets -> core/layout`. `core` ve `layout` widget içe aktarmaz.
- Widget'lar yalnızca `Buffer`'a yazar; stdout'a doğrudan yazan tek yer `DiffWriter.flush` / `Terminal`.
- Widget `render` sözleşmesi: `area` dışına yazma, boş alanda sessizce dön.
- Public API yalnızca `gravitui/__init__.py` üzerinden; yeni sınıfı oraya da ekle.

## Çalışma kuralları
- Her davranış değişikliği için headless test ekle; `python -m unittest discover -s tests -t .` yeşil olmadan commit yok.
- Dosya başına hedef <= 400 satır; core dokümanlar <= 200 satır.
- Cerrahi düzenleme: yalnızca değişen blokları güncelle, yorumları koru.
- Görünür özellik eklenince `CHANGELOG.md` `[Unreleased]` bölümünü güncelle.
- Kullanıcı arayüzü metinleri ve dokümanlar Türkçe, kod tanımlayıcıları İngilizce.
- Yeni worktree/dal açma; ana klasörde ve mevcut dalda çalış.

## Sık komutlar
```powershell
python -m unittest discover -s tests -t .
.\run.ps1 -Example 2
```
