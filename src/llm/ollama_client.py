from __future__ import annotations

import json
import time
from dataclasses import dataclass
import requests
import logging

from src.core.http import build_session

DEPT_LABELS = {
    "isg": "İş Sağlığı ve Güvenliği",
    "ik": "İnsan Kaynakları",
    "muhasebe": "Muhasebe / Vergi / Finans",
    "lojistik": "Lojistik / Dış Ticaret / Gümrük",
    "it_siber": "IT / Siber Güvenlik / Bilgi Güvenliği",
    "kvkk": "KVKK / Kişisel Verilerin Korunması",
}


@dataclass(frozen=True)
class LlmDecision:
    relevant: bool
    confidence: int
    evidence: str
    raw: str


@dataclass(frozen=True)
class MultiDeptDecision:
    isg: bool
    ik: bool
    muhasebe: bool
    lojistik: bool
    it_siber: bool
    kvkk: bool
    confidence: int
    evidence: str
    raw: str


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_s: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s
        self.logger = logging.getLogger(__name__)

    def _post_generate(self, payload: dict) -> str:
        last_err = None
        session = build_session()
        for attempt in range(3):  # 3 deneme
            try:
                # use a short connect timeout and a longer read timeout
                r = session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=(5, self.timeout_s),
                )
                r.raise_for_status()
                return (r.json().get("response") or "").strip()
            except requests.exceptions.RequestException as e:
                last_err = e
                self.logger.warning(
                    "Ollama request failed (attempt %d) %s: %s",
                    attempt + 1,
                    f"{self.base_url}/api/generate",
                    str(e),
                )
                time.sleep(2 + attempt * 2)  # backoff
        if last_err is not None:
            raise RuntimeError(f"Ollama generate failed after retries: {last_err}") from last_err
        raise RuntimeError("Ollama generate failed without an explicit transport error")

    def classify(self, *, department: str, title: str, text: str, url: str = "") -> LlmDecision:
        dept_tr = DEPT_LABELS.get(department, department)
        prompt = _build_prompt(department=dept_tr, title=title, url=url, text=text)

        raw = self._post_generate(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1, "top_p": 0.9},
            }
        )
        return _parse(raw)

    def classify_multi(self, *, title: str, text: str, url: str = "") -> MultiDeptDecision:
        prompt = f"""
Sen bir mevzuat analiz uzmanısın.

Görev:
Aşağıdaki Resmî Gazete içeriği bir fabrikada hangi departmanları etkiler?
Departmanlar: ISG, IK, MUHASEBE, LOJISTIK, IT_SIBER, KVKK

Ön kapı sorusu (zorunlu):
"Bu düzenleme özel sektör işletmelerini (yükümlülük, standart, yeterlilik, uygulama, bilgilendirme) açısından etkiliyor mu?"
- Önce bu soruyu cevapla.
- Cevap HAYIR ise departmanların tamamı false olmalı (isg=false, ik=false, muhasebe=false, lojistik=false, it_siber=false, kvkk=false).
- Cevap EVET ise departmanları ayrı ayrı değerlendir.
- ÖNEMLİ: Ulusal meslek standardı, mesleki yeterlilik, sertifikasyon gibi düzenlemeler ilgili departmanı ETKİLER (EVET). Örneğin yazılım geliştirici meslek standardı IT_SIBER'i etkiler.

Kritik kural:
Başlık ipucu olabilir ama nihai kararı metindeki uygulanabilir yükümlülük/değişiklik/sorumluluk üzerinden ver.

Genel dışlama kuralları:
- İlan/duyuru (vefat, etkinlik, ihale ilanı, üniversite iç yönetmelik vb.) ise genelde hepsi false.
- Belirli proje/il/taşınmaz kamulaştırması ise genelde hepsi false (fabrikayı doğrudan etkilemediği sürece).

Sektörel kurallar:
- Bankacılık/TCMB düzenlemeleri genelde ISG/IK/LOJISTIK=false olabilir; ancak şirket finansını etkilediği için MUHASEBE=true olabilir.
- Kamu kurum içi kadro/atama/teşkilat düzenlemesi genelde hepsi false; istisna: çalışma hayatı/iş hukuku/SGK gibi genel bir yükümlülük içeriyorsa IK=true olabilir.

Departman Tanımları (fabrika bağlamı):
- ISG: iş sağlığı ve güvenliği, 6331, risk değerlendirme, iş kazası, meslek hastalığı, acil durum, OSGB, KKD, yangın güvenliği, çevre kirliliği, atık yönetimi, emisyon, çevresel etki değerlendirmesi (ÇED), tehlikeli atık, iş müfettişi, maruziyet, patlama korunma (ATEX), asbest, gürültü, kimyasal madde vb.
- IK: işe alım, personel, ücret, izin, SGK, çalışma izni, iş kanunu (4857), disiplin, iş sözleşmesi, kıdem/ihbar tazminatı, sendika, toplu iş sözleşmesi, emeklilik, engelli istihdamı, staj, çıraklık, mesleki yeterlilik, mesleki eğitim, İŞKUR, arabuluculuk, iş mahkemesi, bordro, kısa çalışma vb.
- MUHASEBE: vergi, KDV, ÖTV, gelir/kurumlar vergisi, damga vergisi, emlak vergisi, beyanname, BA-BS, teşvik, SGK prim, amortisman, enflasyon muhasebesi, TFRS/TMS, bağımsız denetim, GİB, matrah, stopaj, özelge, TCMB, kur farkı, kâr dağıtımı, tasfiye, konkordato, iflas, serbest bölge, SPK, sermaye piyasası, e-fatura/e-defter/e-arşiv vb.
- LOJISTIK: gümrük, GTIP, ithalat/ihracat, dış ticaret, antrepo, ADR, taşıma, tedarik zinciri, A.TR, EUR.1, navlun, konşimento, konteyner, anti-damping, kota, ürün güvenliği, CE işareti, TSE, kabotaj, deniz ticareti, havacılık, demiryolu, karayolu, özet beyan vb.
- IT_SIBER: siber güvenlik, bilgi güvenliği, bilişim, elektronik haberleşme, BTK, SOME, bilgi teknolojileri, yapay zeka, kripto, dijital dönüşüm, veri merkezi, e-imza, ISO 27001, ERP, SCADA, endüstriyel otomasyon, bulut bilişim, IoT, 5G, e-ticaret, yazılım, sunucu, veritabanı, büyük veri, şifreleme, VPN, SSL/TLS vb.
- KVKK: kişisel veri, KVKK, 6698, veri sorumlusu, veri işleyen, açık rıza, aydınlatma yükümlülüğü, veri ihlali, veri koruma, anonimleştirme, veri aktarımı, veri güvenliği, biyometrik veri, özel nitelikli kişisel veri, GDPR, gizlilik, mahremiyet, kimlik doğrulama, elektronik kimlik vb.

ISG guard:
ISG=true demek için metinde/başlıkta şu kelimelerden en az biri açıkça geçmeli:
iş sağlığı, iş güvenliği, İSG, 6331, OSGB, risk değerlendirme, iş kazası, meslek hastalığı, işyeri hekimi, iş güvenliği uzmanı, KKD, kişisel koruyucu, acil durum, tehlikeli, çalışma ortamı, iş ekipmanı, maruziyet, patlama, ATEX, yüksekte çalışma, asbest, gürültü, kimyasal madde, iş müfettişi, iş teftiş, yangın, ilk yardım, çevre sağlığı, çevre kirliliği, atık yönetimi, atık, çevre izni, ÇED, çevresel etki, emisyon, tehlikeli atık, toplum sağlığı.
Bu kelimeler yoksa ISG=false.

IK guard:
IK=true demek için metinde/başlıkta şu kelimelerden en az biri açıkça geçmeli:
SGK, sosyal güvenlik, istihdam, mesai, fazla çalışma, yıllık izin, ücret, asgari ücret, personel, iş kanunu, 4857, çalışma izni, iş sözleşmesi, kıdem tazminatı, ihbar tazminatı, sendika, toplu iş sözleşmesi, işten çıkarma, fesih, işe iade, emeklilik, prim, sigorta prim, engelli istihdamı, staj, stajyer, çırak, çıraklık, mesleki yeterlilik, mesleki eğitim, disiplin, işçi, işveren, İŞKUR, iş mahkemesi, arabuluculuk, kısa çalışma, ücretsiz izin, bordro.
Bu kelimeler yoksa IK=false.

MUHASEBE guard:
MUHASEBE=true demek için metinde/başlıkta şu kelimelerden en az biri açıkça geçmeli:
vergi, KDV, ÖTV, gelir vergisi, kurumlar vergisi, damga vergisi, emlak vergisi, tevkifat, muhasebe, defter, e-defter, e-fatura, e-arşiv, VUK, vergi usul, faiz, gecikme zammı, harç, beyanname, BA-BS, teşvik, yatırım teşvik, SGK prim, amortisman, enflasyon muhasebesi, enflasyon düzeltmesi, TFRS, TMS, muhasebe standart, bağımsız denetim, GİB, gelir idaresi, matrah, stopaj, özelge, TCMB, merkez bankası, kur farkı, kâr dağıtımı, tasfiye, konkordato, iflas, serbest bölge, vergi indirimi, SPK, sermaye piyasası.
Bu kelimeler yoksa MUHASEBE=false.

Lojistik guard:
LOJISTIK=true demek için metinde/başlıkta şu kelimelerden en az biri açıkça geçmeli:
gümrük, GTİP, gümrük tarife, ithalat, ihracat, dış ticaret, antrepo, A.TR, EUR.1, navlun, konşimento, ADR, taşıma, nakliye, liman, konteyner, serbest ticaret, ticaret anlaşması, anti-damping, damping, korunma önlemi, kota, ürün güvenliği, CE işareti, TSE, Türk standardı, tedarik zinciri, kabotaj, deniz ticareti, havacılık, demiryolu, karayolu, taşıma belgesi, özet beyan, lojistik, taşımacılık, transit, menşe.
Bu kelimeler yoksa LOJISTIK=false.

IT_SIBER guard:
IT_SIBER=true demek için metinde/başlıkta şu kelimelerden en az biri açıkça geçmeli:
siber, bilgi güvenliği, bilişim, BTK, SOME, elektronik haberleşme, yapay zeka, kripto, dijital dönüşüm, veri merkezi, e-imza, ISO 27001, yazılım, yazılım geliştirici, bilgi teknolojileri, IT, bilgisayar, ağ güvenliği, veri tabanı, programlama, mobil uygulama, web geliştirme, sistem yönetimi, bulut bilişim, ERP, SCADA, endüstriyel otomasyon, IoT, nesnelerin interneti, 5G, e-ticaret, elektronik ticaret, sunucu, büyük veri, şifreleme, kriptografi, VPN, SSL, TLS, güvenlik duvarı, zafiyet, sızma testi, siber olay.
Bu kelimeler yoksa IT_SIBER=false.

KVKK guard:
KVKK=true demek için metinde/başlıkta şu kelimelerden en az biri açıkça geçmeli:
KVKK, 6698, kişisel veri, kişisel verilerin korunması, veri sorumlusu, veri işleyen, açık rıza, aydınlatma yükümlülüğü, veri ihlali, veri koruma, anonimleştirme, veri güvenliği, veri işleme, gizlilik politikası, çerez politikası, mahremiyet, biyometrik veri, özel nitelikli kişisel veri, sicil, kayıt sistemi, GDPR, Kişisel Verileri Koruma Kurumu, Kişisel Verileri Koruma Kurulu, veri aktarımı, veri silme, veri yok etme, e-Devlet, kimlik doğrulama, elektronik kimlik, kişisel bilgi, gizlilik, veri tabanı güvenliği.
Bu kelimeler yoksa KVKK=false.

Not: "dış ticaret" ve "ihracat/ithalat" konuları IK değil, LOJISTIK kapsamındadır.

Evidence zorunludur:
Metinden en az bir ifade/kurum adı al ve "fabrikaya etkisini" tek cümlede yaz.
Genel/yuvarlak gerekçe yazma.

Sadece TEK SATIR JSON döndür.

Format:
{{"affects_private_manufacturing_obligations": true/false,
"isg": true/false, "ik": true/false, "muhasebe": true/false, "lojistik": true/false,
"it_siber": true/false, "kvkk": true/false,
"confidence": 0-100, "evidence": "metinden kanıt + fabrikaya etkisi"}}

Başlık: {title}
URL: {url}

METİN:
{text}
""".strip()

        raw = self._post_generate(
            {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0.1, "top_p": 0.9},
            }
        )
        try:
            obj = _parse_json_object(raw)
            affects_obligations = _as_bool(obj.get("affects_private_manufacturing_obligations", True))
            confidence = int(obj.get("confidence", 0))
            evidence = str(obj.get("evidence", "")).strip()

            if not affects_obligations:
                return MultiDeptDecision(
                    isg=False,
                    ik=False,
                    muhasebe=False,
                    lojistik=False,
                    it_siber=False,
                    kvkk=False,
                    confidence=confidence,
                    evidence=evidence,
                    raw=raw,
                )

            return MultiDeptDecision(
                isg=_as_bool(obj.get("isg", False)),
                ik=_as_bool(obj.get("ik", False)),
                muhasebe=_as_bool(obj.get("muhasebe", False)),
                lojistik=_as_bool(obj.get("lojistik", False)),
                it_siber=_as_bool(obj.get("it_siber", False)),
                kvkk=_as_bool(obj.get("kvkk", False)),
                confidence=confidence,
                evidence=evidence,
                raw=raw,
            )
        except Exception:
            return MultiDeptDecision(False, False, False, False, False, False, 0, "", raw)


def _build_prompt(*, department: str, title: str, url: str, text: str) -> str:
    return f"""
Sen bir mevzuat analiz uzmanısın.

Görev:
Aşağıdaki içerik "{department}" departmanını bir fabrikada (uyum/operasyon) etkileyecek bir düzenleme içeriyor mu?

Kurallar:
- İlan/duyuru (vefat, etkinlik, üniversite iç yönetmelik vb.) ise genelde NO.
- Sadece metne dayan.
- Başlık sadece ipucudur; nihai kararı metindeki uygulanabilir yükümlülük/değişiklik/sorumluluk üzerinden ver.
- Sadece bankalar/finansal kuruluşlara yönelik düzenleme ise NO.
- Sadece kamu kurum içi kadro/atama/teşkilat düzenlemesi ise NO.
- Belirli proje/il/taşınmaz kamulaştırması ise (fabrikanın adı geçmiyorsa) NO.
- Cevabı sadece TEK SATIR JSON olarak ver.
Evidence zorunludur: metinden en az bir ifade/kurum adı ve fabrikaya etkisini tek cümlede birlikte yaz.

Format (tek satır JSON):
{{"relevant": true/false, "confidence": 0-100, "evidence": "metinden kanıt + fabrikaya etkisi"}}

Başlık: {title}
URL: {url}

METİN:
{text}
""".strip()


def _parse(raw: str) -> LlmDecision:
    try:
        obj = _parse_json_object(raw)
        return LlmDecision(
            relevant=_as_bool(obj.get("relevant", False)),
            confidence=int(obj.get("confidence", 0)),
            evidence=str(obj.get("evidence", "")).strip(),
            raw=raw,
        )
    except Exception:
        return LlmDecision(False, 0, "", raw)


def _parse_json_object(raw: str) -> dict:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("No JSON object found in LLM response")

    parsed = json.loads(raw[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("LLM response JSON is not an object")
    return parsed


def _as_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "evet"}:
            return True
        if normalized in {"false", "0", "no", "n", "hayır", "hayir", ""}:
            return False
    return False
