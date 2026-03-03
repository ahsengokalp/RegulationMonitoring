from __future__ import annotations

import json
import time
from dataclasses import dataclass
import requests

DEPT_LABELS = {
    "isg": "İş Sağlığı ve Güvenliği",
    "ik": "İnsan Kaynakları",
    "muhasebe": "Muhasebe / Vergi / Finans",
    "lojistik": "Lojistik / Dış Ticaret / Gümrük",
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
    confidence: int
    evidence: str
    raw: str


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_s: int = 240) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout_s = timeout_s

    def _post_generate(self, payload: dict) -> str:
        last_err = None
        for attempt in range(3):  # 3 deneme
            try:
                r = requests.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=self.timeout_s,
                )
                r.raise_for_status()
                return (r.json().get("response") or "").strip()
            except (requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
                last_err = e
                time.sleep(2 + attempt * 2)  # backoff
        if last_err is not None:
            raise last_err
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
Aşağıdaki Resmî Gazete içeriği fabrikada hangi departmanları etkiler?
Departmanlar: ISG, IK, MUHASEBE, LOJISTIK

Kurallar:
- İlan/duyuru (vefat, etkinlik, üniversite iç yönetmelik vb.) ise genelde hepsi false.
- Sadece metne dayan.
- Sadece TEK SATIR JSON döndür.

Departman Tanımları (fabrika bağlamı):
- ISG: iş sağlığı ve güvenliği, 6331, risk değerlendirme, iş kazası, acil durum, OSGB vb.
- IK: işe alım, personel, ücret, izin, SGK, çalışma izni, iş kanunu, disiplin vb.
- MUHASEBE: vergi, KDV, e-fatura/e-defter, finans, faiz, karşılık, muhasebe standartları vb.
- LOJISTIK: gümrük, GTIP, ithalat/ihracat, dış ticaret mevzuatı, antrepo, ADR, taşıma, tedarik vb.

Not: "dış ticaret" ve "ihracat/ithalat" konuları IK değil, LOJISTIK kapsamındadır.

Format:
{{"isg": true/false, "ik": true/false, "muhasebe": true/false, "lojistik": true/false,
"confidence": 0-100, "evidence": "kısa kanıt cümlesi"}}

Başlık: {title}
URL: {url}

Not: Başlık, departman sınıflandırmasında güçlü bir sinyaldir. Metin kısa olsa bile başlığa göre karar verebilirsin.

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
            obj = json.loads(raw[raw.find("{") : raw.rfind("}") + 1])
            return MultiDeptDecision(
                isg=bool(obj.get("isg", False)),
                ik=bool(obj.get("ik", False)),
                muhasebe=bool(obj.get("muhasebe", False)),
                lojistik=bool(obj.get("lojistik", False)),
                confidence=int(obj.get("confidence", 0)),
                evidence=str(obj.get("evidence", "")).strip(),
                raw=raw,
            )
        except Exception:
            return MultiDeptDecision(False, False, False, False, 0, "", raw)


def _build_prompt(*, department: str, title: str, url: str, text: str) -> str:
    return f"""
Sen bir mevzuat analiz uzmanısın.

Görev:
Aşağıdaki içerik "{department}" departmanını bir fabrikada (uyum/operasyon) etkileyecek bir düzenleme içeriyor mu?

Kurallar:
- İlan/duyuru (vefat, etkinlik, üniversite iç yönetmelik vb.) ise genelde NO.
- Sadece metne dayan.
- Cevabı sadece TEK SATIR JSON olarak ver.

Format (tek satır JSON):
{{"relevant": true/false, "confidence": 0-100, "evidence": "metinden kısa kanıt cümlesi"}}

Başlık: {title}
URL: {url}

METİN:
{text}
""".strip()


def _parse(raw: str) -> LlmDecision:
    try:
        s = raw[raw.find("{") : raw.rfind("}") + 1]
        obj = json.loads(s)
        return LlmDecision(
            relevant=bool(obj.get("relevant", False)),
            confidence=int(obj.get("confidence", 0)),
            evidence=str(obj.get("evidence", "")).strip(),
            raw=raw,
        )
    except Exception:
        return LlmDecision(False, 0, "", raw)
