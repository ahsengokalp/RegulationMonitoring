from __future__ import annotations

import re
from typing import List

from src.core.models import GazetteItem
from src.policies.base import DepartmentPolicy, PolicyDecision


HIGH_SIGNAL = [
    r"\bsiber\s*güvenlik\b",
    r"\bsiber\s*saldırı\b",
    r"\bbilgi\s*güvenliği\b",
    r"\bbilişim\b",
    r"\belektronik\s*haberleşme\b",
    r"\bBTK\b",
    r"\bSOME\b",
    r"\bbilgi\s*teknoloji\b",
    r"\bbilgi\s*sistemi\b",
    r"\be-devlet\b",
    r"\byapay\s*zek[aâ]\b",
    r"\bkripto\b|\bblokzincir\b|\bblockchain\b",
    r"\bISO\s*27001\b",
    r"\bağ\s*güvenliği\b",
    r"\bveri\s*ihlali\b",
    r"\bveri\s*merkezi\b",
    r"\bdijital\s*dönüşüm\b",
    r"\belektronik\s*imza\b|\be-imza\b",
    r"\belog\b|\blog\s*kayd\b",
    r"\bsertifika\s*otoritesi\b",
    r"\byazılım\s*geliştirici\b",
    r"\bmobil\s*uygulama\b",
    r"\bweb\s*geliştirme\b",
    r"\bprogramlama\b",
    r"\bbulut\s*bilişim\b",
    r"\bsistem\s*yönetimi\b",
    r"\bERP\b",
    r"\bSCADA\b",
    r"\bendüstriyel\s*otomasyon\b",
    r"\bsiber\s*olay\b",
    r"\bsızma\s*testi\b",
    r"\bzafiyet\b",
    r"\bgüvenlik\s*duvarı\b",
    r"\bşifreleme\b|\bkriptografi\b",
    r"\bSSL\b|\bTLS\b",
    r"\bVPN\b",
    r"\bsunucu\b",
    r"\bveritabanı\b|\bveri\s*tabanı\b",
    r"\bbüyük\s*veri\b",
    r"\bnesnelerin\s*interneti\b|\bIoT\b",
    r"\b5G\b",
    r"\belektronik\s*ticaret\b|\be-ticaret\b",
]

MID_SIGNAL = [
    r"\binternet\b",
    r"\byazılım\b",
    r"\bdijital\b",
    r"\belektronik\b",
    r"\byönetmelik\b",
    r"\btebliğ\b",
    r"\bteknoloji\b",
    r"\bsiber\b",
    r"\botomasyon\b",
]


def _score(text: str) -> tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []
    for pat in HIGH_SIGNAL:
        if re.search(pat, text, flags=re.IGNORECASE):
            score += 10
            reasons.append(f"high:{pat}")
    for pat in MID_SIGNAL:
        if re.search(pat, text, flags=re.IGNORECASE):
            score += 3
            reasons.append(f"mid:{pat}")
    return score, reasons


class ItSiberPolicy(DepartmentPolicy):
    @property
    def name(self) -> str:
        return "it_siber"

    def evaluate_title(self, item: GazetteItem) -> PolicyDecision:
        if item.section and "İLAN" in item.section.upper():
            return PolicyDecision(False, 0, ["section_excluded: İLAN BÖLÜMÜ"])

        haystack = " ".join([x for x in [item.section, item.subsection, item.title] if x])
        score, reasons = _score(haystack)
        return PolicyDecision(is_relevant=score >= 10, score=score, reasons=reasons)
