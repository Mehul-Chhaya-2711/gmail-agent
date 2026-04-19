"""
Streamlit app for Gmail fetch + classification + reports + ambiguous review + Gemini fallback.
"""

import pandas as pd
import streamlit as st

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
st.caption("Step 10: Gemini fallback for ambiguous emails")

st.write("This step adds Gemini classification for ambiguous emails with an LLM hard cap.")

if "last_classified_emails" not in st.session_state:
    st.session_state["last_classified_emails"] = []

scan_size = st.selectbox(
    "Choose scan size",
    options=SCAN_SIZE_OPTIONS,
    index=SCAN_SIZE_OPTIONS.index(INITIAL_EMAIL_FETCH_COUNT),
)

st.caption(f"Current max allowed per run: {MAX_EMAILS_PER_RUN}")
st.caption(f"Current max LLM emails per run: {MAX_LLM_EMAILS_PER_RUN}")

if st.button("Scan, Classify, and Generate Reports"):
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

        st.success(f"Processed {len(classified_emails)} emails and saved reports successfully.")

        st.subheader("Detailed Report Preview")
        st.dataframe(detailed_df, use_container_width=True)

        st.subheader("Summary Report")
        st.dataframe(summary_df, use_container_width=True)

        st.subheader("Category Counts")
        st.dataframe(
            detailed_df["category"].value_counts().rename_axis("category").reset_index(name="count"),
            use_container_width=True,
        )

        st.info("Reports saved to data/reports/ as CSV and Excel.")
    except Exception as exc:
        st.error(f"Error: {exc}")

st.divider()
st.subheader("Process Ambiguous Emails with Gemini")

classified_emails = st.session_state.get("last_classified_emails", [])
ambiguous_before = [
    item for item in classified_emails
    if item["classification"].get("category") == "AMBIGUOUS"
]

st.write(f"Ambiguous emails currently waiting: {len(ambiguous_before)}")

if st.button("Process Ambiguous with Gemini"):
    try:
        with st.spinner("Processing with Gemini (rate-limited, may take ~1–2 minutes)..."):
            llm_processed = process_ambiguous_with_llm(classified_emails)

            summary_df, detailed_df = save_reports(
                classified_emails=classified_emails,
                before_email_count=len(classified_emails),
                after_email_count=len(classified_emails),
            )

        st.success(f"Gemini processed {llm_processed} ambiguous emails.")

        st.subheader("Updated Detailed Report Preview")
        st.dataframe(detailed_df, use_container_width=True)

        st.subheader("Updated Summary Report")
        st.dataframe(summary_df, use_container_width=True)
    except Exception as exc:
        st.error(f"Error during Gemini processing: {exc}")

st.divider()
st.subheader("Review Suggested Categories")

review_items = st.session_state.get("last_classified_emails", [])

if not review_items:
    st.info("No emails loaded in the current session.")
else:
    llm_or_ambiguous = [
        item for item in review_items
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

                col1, col2 = st.columns(2)

                with col1:
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

                with col2:
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
                    classified_emails=review_items,
                    before_email_count=len(review_items),
                    after_email_count=len(review_items),
                )

                st.success("Reports regenerated after review.")
                st.subheader("Updated Detailed Report Preview")
                st.dataframe(detailed_df, use_container_width=True)

                st.subheader("Updated Summary Report")
                st.dataframe(summary_df, use_container_width=True)
            except Exception as exc:
                st.error(f"Error while regenerating reports: {exc}")