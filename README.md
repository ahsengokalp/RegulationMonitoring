# Regülasyon Takip Sistemi

Türkiye Cumhuriyeti Resmî Gazete'de yayımlanan düzenlemeleri günlük olarak takip eden ve fabrika departmanlarına göre sınıflandıran bir web uygulamasıdır.

## Ne İşe Yarar?

Sistem her gün Resmî Gazete'yi tarar ve yayımlanan yönetmelik, tebliğ, kanun gibi düzenlemeleri otomatik olarak analiz eder. Her düzenlemenin hangi departmanı ilgilendirdiğini yapay zeka ile belirler ve ilgili departmanlara e-posta bildirimi gönderir.

Takip edilen departmanlar:
- **Muhasebe** — Vergi, KDV, e-fatura, finans, muhasebe standartları
- **İş Güvenliği (İSG)** — İş sağlığı ve güvenliği, risk değerlendirme, OSGB
- **İnsan Kaynakları (İK)** — İşe alım, SGK, çalışma izni, iş kanunu
- **Lojistik** — Gümrük, ithalat/ihracat, dış ticaret, taşıma
- **IT / Siber Güvenlik** — Bilişim, siber güvenlik, veri merkezi, yazılım
- **KVKK** — Kişisel verilerin korunması, veri sorumlusu, aydınlatma yükümlülüğü

## Dashboard (Ana Ekran)

Uygulamayı tarayıcıdan açtığınızda ana ekranı görürsünüz.

### Departman Kartları

Ekranın üst kısmında her departman için renkli kartlar bulunur. Her kartta o departmanı ilgilendiren düzenleme sayısı gösterilir. Bir karta tıklayarak sadece o departmanın düzenlemelerini filtreleyebilirsiniz. Tekrar tıklayarak filtreyi kaldırabilirsiniz.

### Veri Çekme

**Tek gün çekmek için:** Sağ üstteki tarih alanından istediğiniz günü seçip "Veri Çek" butonuna basın. İşlem arka planda başlar; birkaç dakika sonra sayfayı yenileyerek sonuçları görebilirsiniz.

**Birden fazla gün çekmek için:** "Toplu Çek" butonuna basın. Açılan pencerede başlangıç ve bitiş tarihlerini seçip "Başlat" butonuna basın. Sistem her gün için sırayla veri çeker ve ilerlemeyi canlı olarak gösterir:
- Her günün kaç kayıt bulduğu log alanında görünür
- İlerleme çubuğu tamamlanma yüzdesini gösterir
- İşlemi istediğiniz zaman "Durdur" butonuyla iptal edebilirsiniz
- En fazla 90 günlük aralık seçilebilir

### Arama ve Filtreleme

- **Metin araması:** Arama kutusuna yazdığınız kelime başlık, konu, alt başlık ve detay metninde aranır.
- **Kayıt sayısı:** "Göster" butonlarıyla tabloda kaç kayıt listeleneceğini seçebilirsiniz (50, 100, 200, 500, 1000 veya 2000).
- **Departman filtresi:** Üstteki departman kartlarına tıklayarak filtreleyebilirsiniz.

Bu filtreler birlikte çalışır. Örneğin hem "İSG" kartına tıklayıp hem arama kutusuna "yönetmelik" yazarak dar sonuçlar elde edebilirsiniz.

### Tablo Sütunları

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

### Ayrıntı Görüntüleme

Tablodaki göz simgesine tıkladığınızda düzenlemenin tam metnini bir pencerede görüntüleyebilirsiniz. Bu pencerede:
- Düzenlemenin başlığı
- Resmî Gazete kaynağına bağlantı
- Sayfa içeriği ve varsa PDF eklerinin metni gösterilir

### Veritabanı Yedekleme

Sayfanın en altındaki "Veritabanını Yedekle" butonuyla tüm verilerin bir kopyasını bilgisayarınıza indirebilirsiniz.

## E-posta Bildirimleri

Sistem, bir departmanı ilgilendiren düzenleme bulduğunda o departmanın sorumlu kişilerine otomatik e-posta gönderir. E-postada:
- Hangi düzenlemelerin bulunduğu
- Her düzenlemenin başlığı ve bağlantısı
- Yapay zekanın değerlendirmesi yer alır

Ayrıca her veri çekme işlemi sonrasında yönetici adreslerine durum bildirimi gönderilir (başarılı/başarısız).

## Otomatik Günlük Çalıştırma

Sistem bir sunucuya kurulduğunda her gün belirlenen saatte otomatik olarak çalışacak şekilde ayarlanabilir. Bu sayede düzenlemeler insan müdahalesi olmadan takip edilir ve ilgili kişilere bildirim gider.
