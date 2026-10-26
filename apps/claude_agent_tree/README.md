# ⚡ Claude Code Agent Tree (TUI Edition)

Terminal tabanlı çoklu ajan mimarisi (**Claude Code Agent Tree**) görselinin konsol ve terminal panellerine (**TUI - Terminal User Interface**) uyarlanmış sürümüdür.

---

## 🏛️ Mimari Tasarım (TUI Architecture)

Uygulama, **Model-View-Controller (MVC) / Observer** desenini takip eden, modern `Rich` terminal kütüphanesi üzerine inşa edilmiş zengin bir TUI panel sistemidir.

```
claude_agent_tree_tui/
│
├── main.py                     # TUI giriş noktası, Live alternate buffer döngüsü ve klavye dinleyicisi
├── config.py                   # Konsol boyutları, yenileme ve imleç zamanlama sabitleri
├── run.bat                     # Windows için tek tıkla tam ekran TUI başlatma betiği
│
├── theme/                      # Görsel Sistem ve Tasarım Token'ları
│   ├── colors.py               # Hex TrueColor renk paleti (Opus, JEV, Subagents, Fable)
│   └── __init__.py
│
├── models/                     # Saf Veri Modelleri (UI'dan tamamen izole)
│   ├── agent_state.py          # Opus 5.5 ana oturum ve dönüş kutusu verisi
│   ├── advisor_state.py        # FABLE 5.1 fazları, son tavsiyeler ve sayaçlar
│   ├── fork_metrics.py         # JEV katmanı güvenilirlik skorları ve çubuk hesaplamaları
│   ├── subagent_state.py       # Worker, Explorer, Researcher ajan durumları
│   └── session_log.py          # Terminal log kayıtları veri modeli
│
├── state/                      # Durum Yönetimi
│   └── store.py                # Merkezi veri deposu (Single Source of Truth), simülasyon ve Observer dinleyicileri
│
└── tui/                        # Modüler TUI Bileşenleri
    ├── header.py               # Üst başlık, durum rozetleri ve renk lejantı
    ├── advisor_view.py         # Sol sütun FABLE 5.1 advisor paneli ve faz rozeti
    ├── flow_view.py            # Hiyerarşik ajan akış ağacı, JEV çubukları ve 3 alt ajan
    ├── log_view.py             # Renkli terminal log konsolu
    ├── prompt_view.py          # Yanıp sönen imleçli komut satırı ve durum kapsülleri
    └── dashboard.py            # Responsive Rich Layout orkestrasyonu
```

---

## 🚀 Çalıştırma

1. **Yol 1:** Klasör içindeki `run.bat` dosyasına çift tıklayın.
2. **Yol 2:** Terminal veya PowerShell üzerinden:
   ```bash
   cd "apps/claude_agent_tree"
   python main.py
   ```

---

## ⌨️ İnteraktif Kontroller ve Kısayollar

TUI paneli canlı olarak çalışırken klavyeden şu tuşları kullanabilirsiniz:

| Tuş | Açıklama |
|---|---|
| `Q` veya `Esc` | TUI panelinden temiz bir şekilde çıkış yapar ve terminali eski haline döndürür. |
| `Space` | Alt ajanların çalışma durumunu duraklatır (`⏸ paused`) veya devam ettirir (`◎ running`). |
| `A` | FABLE 5.1 danışman fazını sırayla değiştirir (`before a plan` ➔ `analyzing AST` ➔ `error repeats` ➔ `before done`). |
| `F` | JEV çatallanma katmanında dinamik çatallanma ve güven skoru simülasyonu tetikler. |
| `L` | Canlı oturum günlüğüne (`session log`) yeni bir simülasyon olayı ekler. |

---

## 🎨 Öne Çıkan Özellikler

- **Alternate Screen Buffer:** Terminal geçmişinizi kirletmez (`screen=True`), çıkış yaptığınızda terminal temiz kalır.
- **Düşük Kaynak Kullanımı:** CPU kullanımı <%1 seviyesindedir.
- **Canlı Efektler:**
  - `❯ claude --advisor fable █` komut satırında yanıp sönen gerçekçi terminal imleci.
  - Ajan kartlarında `◎ running` / `◉ running` canlı durum nabzı.
  - JEV güvenilirlik katmanında `[█████████████░] 94% sharp` çubukları.
- **Windows High-DPI & UTF-8:** Windows CMD ve Windows Terminal üzerinde kusursuz kutu çizim karakterleri (`chcp 65001`).
