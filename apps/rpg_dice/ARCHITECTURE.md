# 🏛️ Architecture (RpgDiceTui)

RpgDiceTui, Baldur's Gate 3 ve D&D masaüstü RPG oyunları kalitesinde, terminalde çalışan 24-bit TrueColor sinematik zar simülatörüdür.

## 1. Katman Mimarisi
* **Sunum & 3D Motor (`dice_engine.py`, `colors.py`):**
  * 3D ikosahedron/çokyüzlü geometrileri (d4, d6, d8, d10, d12, d20, d100).
  * Kuaterniyon ve 3D rotasyon matrisleri, perspektif projeksiyon, flat shading ve specular highlight.
* **Mekanik & Kurallar (`mechanics.py`):**
  * DC (Difficulty Class), stat ve yetenek değiştiricileri (Guidance, Bless vb.).
  * Advantage / Disadvantage mantığı.
  * Natural 20 (Critical Success) ve Natural 1 (Critical Failure) tespiti.
* **Efektler & FX (`particles.py`):**
  * Altın patlama şok dalgaları, screen shake (ekran sarsıntısı), kızıl glitch dalgaları.
* **Giriş & Döngü (`main.py`):**
  * 30 FPS titreşimsiz çift tamponlama, klavye kontrolleri ve Windows VT100 etkinleştirme.

## 2. Mimari Kurallar
* **Sıfır Bağımlılık:** Yalnızca Python 3 standart kütüphanesi (`math`, `time`, `os`, `sys`, `msvcrt`, `ctypes`).
* **Hatasız Sonuç:** Zar önce mekanik olarak atılır, ardından fizik motoru zarın tam olarak o yüzün üzerine inmesini sağlar.
