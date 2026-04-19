"""
Safe Gmail actions for the Gmail Cleanup AI Agent.
Only trashes emails that are explicitly allowed by the workflow.
"""

from __future__ import annotations

from typing import Any, Dict, List

from config import DELETE_MODE, SAFE_CATEGORIES


def trash_email(service, email_id: str) -> Dict[str, Any]:
    """
    Move one email to Gmail trash.
    """
    if DELETE_MODE != "trash":
        raise ValueError("Only trash mode is allowed.")

    return service.users().messages().trash(userId="me", id=email_id).execute()


def bulk_trash_emails(service, email_ids: List[str]) -> int:
    """
    Trash multiple emails one by one.
    Returns count successfully trashed.
    """
    trashed_count = 0

    for email_id in email_ids:
        try:
            trash_email(service, email_id)
            trashed_count += 1
        except Exception as exc:
            print(f"Failed to trash {email_id}: {exc}")

    return trashed_count


def get_deletable_emails(classified_emails: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Return only emails that are safe to trash under current policy.
    Current policy:
    - category must be promotions
    - must not belong to safe categories
    """
    deletable = []

    for item in classified_emails:
        classification = item.get("classification", {})
        category = classification.get("category", "")

        if category == "promotions" and category not in SAFE_CATEGORIES:
            deletable.append(item)

    return deletable