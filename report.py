"""
Reporting utilities for the Gmail Cleanup AI Agent.
Creates summary and detailed reports in CSV and Excel format.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

from config import (
    DETAILED_REPORT_CSV_FILE,
    DETAILED_REPORT_FILE,
    SUMMARY_REPORT_FILE,
)


def build_detailed_report_rows(
    classified_emails: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for item in classified_emails:
        email = item["email"]
        classification = item["classification"]

        rows.append(
            {
                "email_id": email.get("email_id", ""),
                "sender": email.get("sender", ""),
                "subject": email.get("subject", ""),
                "date": email.get("date", ""),
                "category": classification.get("category", ""),
                "classification_source": classification.get("classification_source", ""),
                "confidence": classification.get("confidence", ""),
                "action": item.get("action", "kept"),
                "reason": classification.get("reason", ""),
            }
        )

    return rows


def build_summary_report(
    detailed_rows: List[Dict[str, Any]],
    before_email_count: int | None = None,
    after_email_count: int | None = None,
) -> pd.DataFrame:
    df = pd.DataFrame(detailed_rows)

    if df.empty:
        summary = {
            "generated_at": datetime.now().isoformat(),
            "total_emails_scanned": 0,
            "ambiguous_count": 0,
            "llm_processed_count": 0,
            "rule_based_count": 0,
            "memory_based_count": 0,
            "manual_review_count": 0,
            "deleted_emails_count": 0,
            "before_email_count": before_email_count if before_email_count is not None else 0,
            "after_email_count": after_email_count if after_email_count is not None else 0,
        }
        return pd.DataFrame([summary])

    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_emails_scanned": int(len(df)),
        "ambiguous_count": int((df["category"] == "AMBIGUOUS").sum()),
        "llm_processed_count": int((df["classification_source"] == "llm").sum()),
        "rule_based_count": int((df["classification_source"] == "rule").sum()),
        "memory_based_count": int((df["classification_source"] == "memory").sum()),
        "manual_review_count": int((df["classification_source"] == "manual_review").sum()),
        "deleted_emails_count": int((df["action"] == "trashed").sum()),
        "before_email_count": before_email_count if before_email_count is not None else int(len(df)),
        "after_email_count": after_email_count if after_email_count is not None else int(len(df)),
    }

    category_counts = df["category"].value_counts().to_dict()
    for category, count in category_counts.items():
        summary[f"category_{category}_count"] = int(count)

    return pd.DataFrame([summary])


def save_reports(
    classified_emails: List[Dict[str, Any]],
    before_email_count: int | None = None,
    after_email_count: int | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    detailed_rows = build_detailed_report_rows(classified_emails)
    detailed_df = pd.DataFrame(detailed_rows)
    summary_df = build_summary_report(
        detailed_rows,
        before_email_count=before_email_count,
        after_email_count=after_email_count,
    )

    detailed_df.to_csv(DETAILED_REPORT_CSV_FILE, index=False)
    detailed_df.to_excel(DETAILED_REPORT_FILE, index=False)
    summary_df.to_csv(SUMMARY_REPORT_FILE, index=False)

    return summary_df, detailed_df