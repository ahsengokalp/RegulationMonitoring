from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Pattern, Tuple


@dataclass(frozen=True)
class NegativeRule:
    pattern: Pattern[str]
    penalty: int              # -score
    label: str
    hard_exclude: bool = False


def compile_negative_rules(rules: Iterable[Tuple[str, int, str, bool]]) -> List[NegativeRule]:
    """
    rules: (regex, penalty, label, hard_exclude)
    penalty: negative number (e.g., -20)
    """
    compiled: List[NegativeRule] = []
    for rx, penalty, label, hard in rules:
        compiled.append(
            NegativeRule(
                pattern=re.compile(rx, flags=re.IGNORECASE),
                penalty=penalty,
                label=label,
                hard_exclude=hard,
            )
        )
    return compiled


def apply_negative_rules(text: str, rules: List[NegativeRule]) -> tuple[int, List[str], bool]:
    """
    Returns:
      total_penalty (negative int),
      reasons,
      is_hard_excluded
    """
    penalty_total = 0
    reasons: List[str] = []
    hard_excluded = False

    for r in rules:
        if r.pattern.search(text):
            penalty_total += r.penalty
            reasons.append(f"neg:{r.label}({r.penalty})")
            if r.hard_exclude:
                hard_excluded = True

    return penalty_total, reasons, hard_excluded