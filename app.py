"""
Final Streamlit app for Gmail Cleanup AI Agent.
Includes:
- scan + classify
- Gemini fallback
- human review + learning
- promotion preview
- safe trashing
- reports
- simple command shortcuts
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from actions import bulk_trash_emails, get_deletable_emails
from classifier import classify_email
from config import (
    INITIAL_EMAIL_FETCH_COUNT,
    MAX_EMAILS_PER_RUN,
    MAX_LLM_EMAILS_PER_RUN,
    REVIEWABLE_CATEGORIES,
    SCAN_SIZE_OPTIONS,
)
from gmail_service import fetch_emails, get_gmail_service
from llm_classifier import process_ambiguous_with_llm
from memory import learn_sender
from report import save_reports

st.set_page_config(page_title="Gmail Agent", page_icon="📧", layout="wide")

st.title("Gmail Cleanup AI Agent")
st.caption("Cloud-based Gmail cleanup with memory, rules, Gemini fallback, review, and safe trashing")

if "last_classified_emails" not in st.session_state:
    st.session_state["last_classified_emails"] = []

if "last_summary_df" not in st.session_state:
    st.session_state["last_summary_df"] = None

if "last_detailed_df" not in st.session_state:
    st.session_state["last_detailed_df"] = None

scan_size = st.selectbox(
    "Choose scan size",
    options=SCAN_SIZE_OPTIONS,
    index=SCAN_SIZE_OPTIONS.index(INITIAL_EMAIL_FETCH_COUNT),
)

st.caption(f"Current max allowed per run: {MAX_EMAILS_PER_RUN}")
st.caption(f"Current max LLM emails per run: {MAX_LLM_EMAILS_PER_RUN}")

command = st.text_input(
    "Command input",
    placeholder='Examples: "show marketing emails", "clean inbox safely", "scan 100 emails"',
)

col1, col2, col3 = st.columns(3)

with col1:
    scan_clicked = st.button("Scan Emails")

with col2:
    process_llm_clicked = st.button("Process Ambiguous")

with col3:
    delete_promotions_clicked = st.button("Delete Promotions Safely")

if command:
    cmd = command.strip().lower()
    if "show marketing" in cmd:
        st.info('Shortcut recognized: showing promotional candidates below.')
    elif "clean inbox safely" in cmd:
        st.info('Shortcut recognized: scan, review promotions, then trash only promotions.')
    elif "scan" in cmd:
        st.info("Shortcut recognized. Use the scan button to execute the run.")

if scan_clicked:
    try:
        with st.spinner(f"Fetching and processing {scan_size} emails..."):
            service = get_gmail_service()
            emails = fetch_emails(service, max_results=min(scan_size, MAX_EMAILS_PER_RUN))

            classified_emails = []
            for email in emails:
                classification = classify_email(email)
                classified_emails.append(
                    {
                        "email": email,
                        "classification": classification,
                        "action": "kept",
                    }
                )

            st.session_state["last_classified_emails"] = classified_emails

            summary_df, detailed_df = save_reports(
                classified_emails=classified_emails,
                before_email_count=len(emails),
                after_email_count=len(emails),
            )

            st.session_state["last_summary_df"] = summary_df
            st.session_state["last_detailed_df"] = detailed_df

        st.success(f"Processed {len(classified_emails)} emails and saved reports successfully.")
    except Exception as exc:
        st.error(f"Error during scan: {exc}")

classified_emails = st.session_state.get("last_classified_emails", [])
summary_df = st.session_state.get("last_summary_df")
detailed_df = st.session_state.get("last_detailed_df")

if process_llm_clicked:
    try:
        with st.spinner("Processing with Gemini (rate-limited, may take ~1–3 minutes)..."):
            llm_processed = process_ambiguous_with_llm(classified_emails)

            summary_df, detailed_df = save_reports(
                classified_emails=classified_emails,
                before_email_count=len(classified_emails),
                after_email_count=len(classified_emails),
            )

            st.session_state["last_summary_df"] = summary_df
            st.session_state["last_detailed_df"] = detailed_df

        st.success(f"Gemini processed {llm_processed} ambiguous emails.")
    except Exception as exc:
        st.error(f"Error during Gemini processing: {exc}")

if delete_promotions_clicked:
    try:
        service = get_gmail_service()
        deletable_items = get_deletable_emails(classified_emails)
        email_ids = [item["email"]["email_id"] for item in deletable_items]

        trashed_count = bulk_trash_emails(service, email_ids)

        trashed_ids = set(email_ids[:trashed_count])
        for item in classified_emails:
            if item["email"]["email_id"] in trashed_ids:
                item["action"] = "trashed"

        before_count = len(classified_emails)
        after_count = before_count - trashed_count

        summary_df, detailed_df = save_reports(
            classified_emails=classified_emails,
            before_email_count=before_count,
            after_email_count=after_count,
        )

        st.session_state["last_summary_df"] = summary_df
        st.session_state["last_detailed_df"] = detailed_df

        st.success(f"Safely moved {trashed_count} promotional emails to Gmail trash.")
    except Exception as exc:
        st.error(f"Error during safe trashing: {exc}")

if detailed_df is not None and not detailed_df.empty:
    st.divider()
    st.subheader("Summary Report")
    st.dataframe(summary_df, use_container_width=True)

    st.subheader("Category Counts")
    st.dataframe(
        detailed_df["category"].value_counts().rename_axis("category").reset_index(name="count"),
        use_container_width=True,
    )

    st.subheader("Detailed Report Preview")
    st.dataframe(detailed_df, use_container_width=True)

st.divider()
st.subheader("Review Suggested Categories")

if not classified_emails:
    st.info("No emails loaded in the current session.")
else:
    llm_or_ambiguous = [
        item for item in classified_emails
        if item["classification"].get("classification_source") in {"llm", "manual_review"}
        or item["classification"].get("category") == "AMBIGUOUS"
    ]

    if not llm_or_ambiguous:
        st.info("No LLM-reviewed or ambiguous emails to review.")
    else:
        st.write(f"{len(llm_or_ambiguous)} emails available for review.")

        for idx, item in enumerate(llm_or_ambiguous):
            email = item["email"]
            current_classification = item["classification"]
            current_category = current_classification.get("category", "AMBIGUOUS")

            default_index = 0
            if current_category in REVIEWABLE_CATEGORIES:
                default_index = REVIEWABLE_CATEGORIES.index(current_category)

            with st.expander(f"Review email {idx + 1}: {email.get('subject', '(no subject)')}"):
                st.write(f"**Sender:** {email.get('sender', '')}")
                st.write(f"**Date:** {email.get('date', '')}")
                st.write(f"**Snippet:** {email.get('snippet', '')}")
                st.write(f"**Current suggestion:** {current_category}")
                st.write(f"**Source:** {current_classification.get('classification_source', '')}")
                st.write(f"**Reason:** {current_classification.get('reason', '')}")

                selected_category = st.selectbox(
                    f"Choose category for email {idx + 1}",
                    REVIEWABLE_CATEGORIES,
                    index=default_index,
                    key=f"review_category_{idx}",
                )

                memory_mode = st.radio(
                    f"Learn using",
                    options=["domain", "full_email"],
                    index=0,
                    horizontal=True,
                    key=f"review_memory_mode_{idx}",
                )

                c1, c2 = st.columns(2)

                with c1:
                    if st.button(f"Approve and Learn email {idx + 1}", key=f"review_approve_{idx}"):
                        use_domain = memory_mode == "domain"
                        learned_key = learn_sender(
                            sender=email.get("sender", ""),
                            category=selected_category,
                            use_domain=use_domain,
                        )

                        item["classification"] = {
                            "category": selected_category,
                            "classification_source": "memory",
                            "confidence": 1.0,
                            "reason": f"Human-approved and learned into memory using key: {learned_key}",
                        }

                        st.success(
                            f"Saved to memory as '{learned_key}' → '{selected_category}'. "
                            f"Future similar emails should avoid LLM review."
                        )

                with c2:
                    if st.button(f"Reclassify only email {idx + 1}", key=f"review_reclassify_{idx}"):
                        item["classification"] = {
                            "category": selected_category,
                            "classification_source": "manual_review",
                            "confidence": 1.0,
                            "reason": "Human-reviewed for this email only; not learned into memory",
                        }

                        st.success("Email reclassified for this session only. Memory not updated.")

        if st.button("Regenerate Reports After Review"):
            try:
                summary_df, detailed_df = save_reports(
                    classified_emails=classified_emails,
                    before_email_count=len(classified_emails),
                    after_email_count=len(classified_emails),
                )
                st.session_state["last_summary_df"] = summary_df
                st.session_state["last_detailed_df"] = detailed_df

                st.success("Reports regenerated after review.")
            except Exception as exc:
                st.error(f"Error while regenerating reports: {exc}")

st.divider()
st.subheader("Promotional Emails Ready for Safe Cleanup")

if classified_emails:
    deletable_items = get_deletable_emails(classified_emails)

    if not deletable_items:
        st.info("No promotional emails currently marked as safe for trashing.")
    else:
        preview_rows = []
        for item in deletable_items:
            email = item["email"]
            classification = item["classification"]
            preview_rows.append(
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

        preview_df = pd.DataFrame(preview_rows)
        st.write(f"{len(preview_df)} promotional emails are eligible for safe trashing.")
        st.dataframe(preview_df, use_container_width=True)
else:
    st.info("Scan emails first to preview promotional cleanup candidates.")