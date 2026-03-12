# Regülasyon Takip Sistemi

Türkiye Cumhuriyeti Resmî Gazete'de yayımlanan düzenlemeleri günlük olarak takip eden ve departmanlara göre sınıflandıran bir web uygulamasıdır.

## Ne İşe Yarar?

Sistem her gün Resmî Gazete'yi tarar ve yayımlanan yönetmelik, tebliğ, kanun gibi düzenlemeleri otomatik olarak analiz eder. Her düzenlemenin hangi departmanı ilgilendirdiğini yapay zeka ile belirler ve ilgili departmanlara e-posta bildirimi gönderir.

Takip edilen departmanlar:

| Departman | Kapsam |
|-----------|--------|
| **Muhasebe** | Vergi, KDV, ÖTV, e-fatura/e-defter, beyanname, teşvik, TFRS/TMS, bağımsız denetim, SPK, matrah, stopaj, konkordato |
| **İş Güvenliği (İSG)** | İş sağlığı ve güvenliği, risk değerlendirme, OSGB, yangın güvenliği, çevre kirliliği, atık yönetimi, emisyon, ÇED, tehlikeli atık, maruziyet, ATEX |
| **İnsan Kaynakları (İK)** | İşe alım, SGK, çalışma izni, iş kanunu, kıdem/ihbar tazminatı, sendika, emeklilik, engelli istihdamı, mesleki yeterlilik, İŞKUR, arabuluculuk |
| **Lojistik** | Gümrük, ithalat/ihracat, dış ticaret, GTIP, antrepo, ADR, taşıma, CE işareti, TSE, anti-damping, tedarik zinciri, kabotaj |
| **IT / Siber Güvenlik** | Bilişim, siber güvenlik, veri merkezi, yazılım, ERP, SCADA, IoT, 5G, e-ticaret, VPN, büyük veri, yapay zeka, dijital dönüşüm |
| **KVKK** | Kişisel verilerin korunması, veri sorumlusu, aydınlatma yükümlülüğü, veri ihlali, GDPR, biyometrik veri, açık rıza |

---

## Ana Ekran (Dashboard)

Uygulamayı tarayıcıdan açtığınızda ana ekranı görürsünüz.

### Bilgi Çubuğu

Ekranın üst kısmında şu bilgiler gösterilir:

- **Son Kontrol** — Sistemin en son ne zaman veri çektiği
- **Toplam** — Veritabanındaki toplam kayıt sayısı
- **Gösterilen** — Şu an tabloda görüntülenen kayıt sayısı
- **Kontrol Sıklığı** — Otomatik kontrol aralığı

### Departman Kartları

Her departman için renkli kartlar bulunur. Her kartta o departmanı ilgilendiren düzenleme sayısı gösterilir.

- Bir karta tıklayarak sadece o departmanın düzenlemelerini filtreleyebilirsiniz
- Tekrar tıklayarak filtreyi kaldırabilirsiniz

---

## Veri Çekme

### Tek Gün

Sağ üstteki tarih alanından istediğiniz günü seçip **"Veri Çek"** butonuna basın. İşlem arka planda başlar; birkaç dakika sonra sayfayı yenileyerek sonuçları görebilirsiniz.

### Toplu Çekme

**"Toplu Çek"** butonuna basarak birden fazla günü sırayla çekebilirsiniz:

1. Açılan pencerede **başlangıç** ve **bitiş** tarihlerini seçin
2. **"Başlat"** butonuna basın
3. Sistem her gün için sırayla veri çeker

Toplu çekme sırasında:
- Daha önce çekilmiş günler otomatik olarak **atlanır**
- Her günün kaç kayıt bulduğu log alanında görünür
- İlerleme çubuğu tamamlanma yüzdesini gösterir
- Hata durumunda sistem otomatik olarak **5 kez yeniden dener**
- İşlemi istediğiniz zaman **"Durdur"** butonuyla iptal edebilirsiniz
- En fazla **90 günlük** aralık seçilebilir

---

## Arama ve Filtreleme

- **Metin araması** — Arama kutusuna yazdığınız kelime başlık, konu, alt başlık ve detay metninde aranır
- **Kayıt sayısı** — "Göster" butonlarıyla tabloda kaç kayıt listeleneceğini seçebilirsiniz (50, 100, 200, 500, 1000 veya 2000)
- **Departman filtresi** — Üstteki departman kartlarına tıklayarak filtreleyebilirsiniz

Bu filtreler birlikte çalışır. Örneğin hem "İSG" kartına tıklayıp hem arama kutusuna "yönetmelik" yazarak sonuçları daraltabilirsiniz.

---

## Tablo Sütunları

| Sütun | Açıklama |
|-------|----------|
| **Tarih** | Düzenlemenin Resmî Gazete'de yayımlandığı tarih |
| **Başlık** | Düzenlemenin adı |
| **Alt Başlık** | Kategori (Yönetmelikler, Tebliğler, vb.) |
| **Konu** | Bölüm (Yürütme ve İdare Bölümü, Yargı Bölümü, vb.) |
| **Kaynak** | Resmî Gazete sayfasına doğrudan bağlantı |
| **PDF** | Düzenleme PDF eki içeriyorsa kırmızı PDF simgesi görünür |
| **Departmanlar** | İlgili departmanlar renkli etiketlerle gösterilir |
| **Ayrıntı** | Detay metni varsa göz simgesine tıklayarak içeriği okuyabilirsiniz |

---

## Ayrıntı Görüntüleme

Tablodaki göz simgesine tıkladığınızda düzenlemenin tam metnini bir pencerede görüntüleyebilirsiniz. Bu pencerede:

- Düzenlemenin başlığı
- Resmî Gazete kaynağına bağlantı
- Sayfa içeriği ve varsa PDF eklerinin metni gösterilir

---

## E-posta Bildirimleri

Sistem, bir departmanı ilgilendiren düzenleme bulduğunda o departmanın sorumlu kişilerine otomatik e-posta gönderir. E-postada:

- Hangi düzenlemelerin bulunduğu
- Her düzenlemenin başlığı ve bağlantısı
- Yapay zekanın değerlendirmesi yer alır

Her veri çekme işlemi sonrasında yönetici adreslerine durum bildirimi (başarılı/başarısız) gönderilir.

---

## Veritabanı Yedekleme

Sayfanın en altındaki **"Veritabanını Yedekle"** butonuyla tüm verilerin bir kopyasını bilgisayarınıza indirebilirsiniz.

---

## Otomatik Günlük Çalıştırma

Sistem bir sunucuya kurulduğunda her gün belirlenen saatte otomatik olarak çalışacak şekilde ayarlanabilir. Bu sayede düzenlemeler insan müdahalesi olmadan takip edilir ve ilgili kişilere bildirim gider.
