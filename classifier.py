"""
Classification logic for the Gmail Cleanup AI Agent.

Decision hierarchy:
1. Memory
2. Rule-based
3. LLM fallback (later)
"""

from __future__ import annotations

import re
from typing import Any, Dict

from memory import load_memory, lookup_memory


PROMOTION_KEYWORDS = [
    "sale",
    "discount",
    "offer",
    "deals",
    "coupon",
    "limited time",
    "buy now",
    "exclusive",
    "clearance",
    "price alert",
]

BANK_KEYWORDS = [
    "bank",
    "account statement",
    "credit card",
    "debit card",
    "transaction",
    "otp",
    "security alert",
    "net banking",
    "upi",
    "insurance",
    "mutual fund",
]

JOB_KEYWORDS = [
    "job",
    "hiring",
    "application",
    "recruiter",
    "interview",
    "resume",
    "career",
    "opportunity",
    "candidate",
    "naukri",
    "indeed",
]

UTILITY_KEYWORDS = [
    "electricity bill",
    "water bill",
    "gas bill",
    "broadband",
    "internet bill",
    "mobile bill",
    "recharge",
    "utility",
    "payment due",
]

PERSONAL_KEYWORDS = [
    "family",
    "friend",
    "wedding",
    "birthday",
    "personal",
]


def _normalize_text(email_record: Dict[str, Any]) -> str:
    """
    Build a single searchable text block from an email record.
    """
    subject = email_record.get("subject", "") or ""
    sender = email_record.get("sender", "") or ""
    snippet = email_record.get("snippet", "") or ""
    body = email_record.get("body", "") or ""

    return f"{sender} {subject} {snippet} {body}".lower()


def _contains_any(text: str, keywords: list[str]) -> bool:
    """
    Return True if any keyword appears in text.
    """
    return any(keyword.lower() in text for keyword in keywords)


def classify_email(email_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify one email using memory first, then rules.

    Returns:
        Dict with category, classification_source, confidence, reason
    """
    sender = email_record.get("sender", "") or ""
    memory_data = load_memory()

    memory_match = lookup_memory(sender, memory_data)
    if memory_match:
        return {
            "category": memory_match,
            "classification_source": "memory",
            "confidence": 0.99,
            "reason": f"Matched memory rule for sender: {sender}",
        }

    searchable_text = _normalize_text(email_record)

    if _contains_any(searchable_text, BANK_KEYWORDS):
        return {
            "category": "bank",
            "classification_source": "rule",
            "confidence": 0.90,
            "reason": "Matched bank-related keywords",
        }

    if _contains_any(searchable_text, JOB_KEYWORDS):
        return {
            "category": "job",
            "classification_source": "rule",
            "confidence": 0.90,
            "reason": "Matched job-related keywords",
        }

    if _contains_any(searchable_text, UTILITY_KEYWORDS):
        return {
            "category": "utility",
            "classification_source": "rule",
            "confidence": 0.88,
            "reason": "Matched utility-related keywords",
        }

    if _contains_any(searchable_text, PROMOTION_KEYWORDS):
        return {
            "category": "promotions",
            "classification_source": "rule",
            "confidence": 0.85,
            "reason": "Matched promotional keywords",
        }

    if _contains_any(searchable_text, PERSONAL_KEYWORDS):
        return {
            "category": "personal",
            "classification_source": "rule",
            "confidence": 0.75,
            "reason": "Matched personal keywords",
        }

    return {
        "category": "AMBIGUOUS",
        "classification_source": "rule",
        "confidence": 0.50,
        "reason": "No clear memory or rule match",
    }