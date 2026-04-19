"""
Memory management for the Gmail Cleanup AI Agent.

Stores human-verified classifications so future runs can reuse them.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, Optional

from config import MEMORY_FILE


def ensure_memory_file() -> None:
    """
    Ensure the memory file exists.
    """
    memory_path = Path(MEMORY_FILE)
    memory_path.parent.mkdir(parents=True, exist_ok=True)

    if not memory_path.exists():
        memory_path.write_text("{}", encoding="utf-8")


def load_memory() -> Dict[str, str]:
    """
    Load saved memory mappings.

    Returns:
        Dict mapping sender email/domain patterns to category labels.
    """
    ensure_memory_file()

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data
        return {}
    except Exception:
        return {}


def save_memory(memory_data: Dict[str, str]) -> None:
    """
    Save memory mappings to disk.
    """
    ensure_memory_file()

    with open(MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(memory_data, f, indent=2, ensure_ascii=False)


def lookup_memory(sender: str, memory_data: Dict[str, str]) -> Optional[str]:
    """
    Match a sender against saved memory keys.

    Matching logic:
    - exact sender match
    - partial substring match
    """
    sender_lower = (sender or "").strip().lower()

    if not sender_lower:
        return None

    if sender_lower in memory_data:
        return memory_data[sender_lower]

    for known_key, category in memory_data.items():
        known_key_lower = known_key.strip().lower()
        if known_key_lower and known_key_lower in sender_lower:
            return category

    return None


def extract_sender_email(sender: str) -> str:
    """
    Extract plain email address from a sender string like:
    'Amazon <store-news@amazon.in>'
    """
    sender = (sender or "").strip().lower()
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', sender)
    return match.group(0) if match else sender


def extract_sender_domain(sender: str) -> str:
    """
    Extract domain from sender email.
    """
    email = extract_sender_email(sender)
    if "@" in email:
        return email.split("@", 1)[1]
    return email


def add_memory_entry(sender_key: str, category: str) -> None:
    """
    Add or update one memory mapping.
    """
    memory_data = load_memory()
    memory_data[sender_key.strip().lower()] = category
    save_memory(memory_data)


def learn_sender(sender: str, category: str, use_domain: bool = True) -> str:
    """
    Learn a sender pattern into memory.

    If use_domain is True, store domain-level memory like 'amazon.in'.
    Otherwise, store full sender email.

    Returns:
        The saved memory key.
    """
    key = extract_sender_domain(sender) if use_domain else extract_sender_email(sender)
    add_memory_entry(key, category)
    return key