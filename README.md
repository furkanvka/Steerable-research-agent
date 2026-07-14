# Steerable-research-agent

Bu proje, yerel yapay zeka modelleri ( ve yerel arama motoru  entegrasyonu ile çalışan, **insan onaylı (Human-in-the-Loop)**, doğrusal bir araştırma ve arama ajanıdır. Ajanın yönetim akışı **LangGraph** (StateGraph) ile tasarlanmıştır.

## Proje Mimarisi ve İş Akışı

Ajanın çalışma mantığı, doğrusal bir grafik yapısı (`StateGraph`) üzerine kuruludur. İş akışı şu düğümlerden (nodes) oluşur:

1. **`plan` (Planlama Düğümü):** Kullanıcı sorgusunu alıp Ollama üzerindeki yerel LLM'e (örn: `qwen3:8b`) gönderir ve konuyu araştırmak üzere 3-5 adet odaklanmış alt başlık oluşturur.
2. **`human_review` (İnsan Onayı):** Grafik `interrupt_before` parametresi sayesinde bu düğümden önce otomatik olarak duraklar. Kullanıcı arayüz üzerinden planlanan alt başlıkları düzenleyebilir, silebilir/atlayabilir veya onaylayabilir. Ayrıca planı baştan oluşturulması için dil modeline geri gönderebilir (`regenerate`).
3. **`search` (Arama Düğümü):** İnsan onayından geçen alt başlıkları paralel olarak **SearXNG** arama motoru üzerinde aratır. Sonuçları toplayıp birleştirir.
4. **`compress` (Sıkıştırma Düğümü):** Elde edilen tüm arama sonuçlarını URL bazında tekilleştirir, temizler ve derlenmiş bir bağlam (context) haline getirir.
5. **`summarize` (Özetleme Düğümü):** Tekilleştirilmiş ve sıkıştırılmış kaynakları kullanarak araştırma konusuna dair nihai Markdown formatında bir özet oluşturur ve akışı sonlandırır (`END`).

## Kurulum ve Çalıştırma

Projeyi yerel bilgisayarınızda ayağa kaldırmak için aşağıdaki adımları takip edebilirsiniz:

### 1. Ön Gereksinimler
* Docker ve Docker Compose'un bilgisayarınızda yüklü olması gerekir.
* Eğer GPU kullanacaksanız, sisteminizde NVIDIA Container Toolkit kurulu olmalıdır.

### 2. Modeli İndirme (Ollama)
Docker konteynerleri çalıştırıldıktan sonra Ollama içinde kullanacağınız varsayılan modeli indirmelisiniz:
```bash
docker exec -it <ollama_konteyner_id> ollama run qwen3:8b
```
*(Varsayılan olarak `backend/app/core/config.py` içinde `OLLAMA_MODEL` değeri `qwen3:8b` olarak belirlenmiştir. Farklı bir model kullanmak isterseniz backend başlatma parametrelerinden veya arayüzden seçebilirsiniz.)*

### 3. Uygulamayı Başlatma
Proje dizininde terminali açıp şu komutu çalıştırın:
```bash
docker compose up -d --build
```

### 4. Arayüze Erişim
Konteynerler başarıyla çalıştıktan sonra tarayıcınızdan şu adrese giderek arayüzü kullanmaya başlayabilirsiniz:
* **Uygulama Arayüzü:** [http://localhost:8000/](http://localhost:8000/)
* **FastAPI Otomatik Dokümantasyonu (Swagger UI):** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## API ve WebSocket Uç Noktaları

### REST API Uç Noktaları

* **`POST /api/research/start`**
  * Yeni bir araştırma oturumu başlatır.
  * **İstek Gövdesi (Request Body):**
    ```json
    {
      "query": "Yapay zekanın geleceği",
      "model": "qwen3:8b",
      "max_iterations": 3
    }
    ```
  * **Yanıt Gövdesi (Response Body):**
    ```json
    {
      "session_id": "uuid-degeri",
      "websocket_url": "ws://localhost:8000/api/ws/research/uuid-degeri"
    }
    ```

* **`GET /api/research/status/{session_id}`**
  * Belirtilen oturumun güncel durumunu (örneğin planlanan başlıklar, mevcut iterasyon, nihai özet) döndürür.

* **`POST /api/research/resume/{session_id}`**
  * **Yedek (Fallback) Kanalı:** İletişim kopmaları, mobil uygulamalarda yeniden bağlanma (reconnect) veya WebSocket'in desteklenmediği senaryolarda insan kararını iletip grafiği devam ettirir.
  * *Önemli Mimari Not:* Aynı oturum (`thread_id`) üzerinde oluşabilecek yarış koşullarını (race condition) ve veri çakışmalarını önlemek amacıyla, WebSocket bağlantısı etkinken tüm onay/düzenleme işlemleri doğrudan WebSocket üzerinden yürütülmelidir. REST `/resume` uç noktası yalnızca bir **fallback** olarak tasarlanmıştır.

### WebSocket Uç Noktası

* **`WS /api/ws/research/{session_id}`**
  * **Birincil İletişim Kanalı:** Araştırma sürecinin her düğümünden (node) üretilen olayları ve canlı durumları anlık izlemek ve insan onay adımlarında etkileşimi yönetmek için kullanılır.
  * **İnsan Onayı (Human-in-the-Loop) Karar Protokolü:**
    Grafik `awaiting_human` durumuna geçip durduğunda, istemci WebSocket üzerinden aşağıdaki formatta bir JSON kararı göndererek grafiği devam ettirir:
    ```json
    {
      "human_feedback": "approved",
      "approved_plan": ["başlık1", "başlık2", "yeni_başlık"]
    }
    ```
    
    **Karar Seçenekleri (`human_feedback` değerleri):**
    *   **`"approved"`:** Modelin ürettiği plan değiştirilmeden onaylanmıştır. Grafik doğrudan arama (`search`) adımına geçer.
    *   **`"edit"`:** Kullanıcı plan üzerinde düzenleme yapmıştır (başlık metnini değiştirmiş, yeni başlık eklemiş veya listeden başlıkları silmiştir). Grafik, yapay zekaya tekrar danışmadan **doğrudan** bu güncellenmiş başlıklarla arama (`search`) adımına ilerler.
    
    **Alt Başlık Atlama ve Ekleme Mekanizması:**
    *   **Atlama/Silme:** Kullanıcı araştırılmasını istemediği bir başlığı arayüzden sildiğinde, bu başlık `approved_plan` listesinden çıkarılmış olur.
    *   **Ekleme:** Kullanıcı yeni bir araştırma başlığı girmek istediğinde arayüzdeki "Yeni Başlık Ekle" butonu ile boş bir satır oluşturup kendi özel alt başlığını tanımlayabilir.
    *   Arama düğümü, kendisine iletilen son `approved_plan` listesindeki başlıkları esas alarak devam eder.
