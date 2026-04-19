"""
Gemini fallback classification for ambiguous emails.
Only used for emails not resolved by memory or rules.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import google.generativeai as genai

from config import GEMINI_MODEL, MAX_LLM_EMAILS_PER_RUN, REVIEWABLE_CATEGORIES, USE_LLM
from utils import safe_json_load


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set in the environment.")

    genai.configure(api_key=api_key)
    return genai.GenerativeModel(GEMINI_MODEL)


def build_llm_prompt(email_record: Dict[str, Any]) -> str:
    allowed_categories = ", ".join(REVIEWABLE_CATEGORIES)

    return f"""
You are classifying a Gmail message into exactly one category.

Allowed categories:
{allowed_categories}

Return valid JSON only in this exact structure:
{{
  "category": "one of the allowed categories",
  "confidence": 0.0,
  "reason": "short reason"
}}

Rules:
- Pick exactly one allowed category
- Confidence must be between 0 and 1
- Do not return markdown
- Do not return extra text

Email data:
Sender: {email_record.get("sender", "")}
Subject: {email_record.get("subject", "")}
Date: {email_record.get("date", "")}
Snippet: {email_record.get("snippet", "")}
Body: {email_record.get("body", "")[:3000]}
""".strip()


def classify_with_llm(email_record: Dict[str, Any]) -> Dict[str, Any]:
    if not USE_LLM:
        return {
            "category": "AMBIGUOUS",
            "classification_source": "llm",
            "confidence": 0.0,
            "reason": "LLM disabled",
        }

    model = get_gemini_client()
    prompt = build_llm_prompt(email_record)
    response = model.generate_content(prompt)

    raw_text = getattr(response, "text", "") or ""
    parsed = safe_json_load(raw_text)

    category = parsed.get("category", "AMBIGUOUS")
    confidence = parsed.get("confidence", 0.60)
    reason = parsed.get("reason", "Gemini classified this email")

    if category not in REVIEWABLE_CATEGORIES:
        category = "AMBIGUOUS"

    try:
        confidence = float(confidence)
    except Exception:
        confidence = 0.60

    confidence = max(0.0, min(confidence, 1.0))

    return {
        "category": category,
        "classification_source": "llm",
        "confidence": confidence,
        "reason": reason,
    }


import time


def process_ambiguous_with_llm(classified_emails: List[Dict[str, Any]]) -> int:
    """
    Process ambiguous emails using Gemini with rate limiting.
    Respects free-tier limits (5 requests per minute).
    """

    processed = 0

    for item in classified_emails:
        classification = item.get("classification", {})

        if classification.get("category") != "AMBIGUOUS":
            continue

        if processed >= MAX_LLM_EMAILS_PER_RUN:
            break

        try:
            llm_result = classify_with_llm(item["email"])
            item["classification"] = llm_result
            processed += 1

            # 🔑 CRITICAL: rate limiting
            time.sleep(12)  
            # 60 sec / 5 requests = 12 sec per request

        except Exception as e:
            print(f"LLM error: {e}")
            continue

    return processed