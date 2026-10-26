# 🤖 Agents Constitution (RpgDiceTui)

Bu repo, Triad otonom ekibi tarafından geliştirilmektedir.

## 1. Temel Standartlar
* **Tek Sorumluluk:** `dice_engine.py` yalnızca 3D matematiği ve projeksiyonu yönetir, `mechanics.py` ise oyun kurallarını denetler. Sorumluluklar birbirine karıştırılamaz.
* **0 Harici Bağımlılık:** Standart kütüphane haricinde harici paket yüklenemez.
* **Titreşimsiz Çizim:** `ScreenBuffer` üzerinden çift tamponlu çizim yapılır.

## 2. Doğrulama ve Bitiş Tanımı (Definition of Done)
* Tüm değişikliklerden sonra `python test_rpg.py` çalıştırılmalı ve 15 testin tamamı firesiz geçmelidir.
* `python -m py_compile` ile sözdizimi doğrulanmalıdır.
* Değişiklikler commit edildikten sonra `git push` ile uzak depoya gönderilmelidir.
