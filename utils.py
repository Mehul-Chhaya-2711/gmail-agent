"""
Utility helpers for the Gmail Cleanup AI Agent.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict


def safe_json_load(text: str) -> Dict[str, Any]:
    """
    Try to extract and parse JSON from model output safely.
    """
    text = (text or "").strip()

    if not text:
        return {}

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except Exception:
            return {}

    return {}