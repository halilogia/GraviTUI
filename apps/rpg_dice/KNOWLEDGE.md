# 🧠 Knowledge (RpgDiceTui)

Projenin kalıcı mühendislik hafızası ve mimari kararları.

## 1. Kararlar ve Gotchas
* **ADR-01: Hedefe İnen Rotasyon (Goal-Oriented Slerp):** Fizik simülasyonunda zarın rastgele durmasını beklemek yerine, mekanik olarak zar atılır ve kuaterniyon interpolasyonu (slerp) ile zar son evrede tam o yüzün üzerine oturtulur.
* **ADR-02: Windows Argüman Kaçışı:** `%~dp0` ters bölü ile bittiğinde `wt.exe -d "%DIR%"` çağrısı `\"` kaçış hatası vererek `0x80070002` hatası oluşturur. `cd /d "%~dp0"` ve `-d "%CD%"` kullanımı esastır.
* **ADR-03: Bağımsız Pencere İzolasyonu:** Arka planda çalışan diğer TUI'lerle çakışmaması için `wt.exe -w new` parametresi varsayılan yapılmıştır.
