from __future__ import annotations

from typing import Any, Dict

from .mapper import to_candidate_payload
from .schemas import AutofillResult


def build_candidate_update(extracted: AutofillResult) -> Dict[str, Any]:
    return to_candidate_payload(extracted)
