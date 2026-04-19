"""
Streamlit app for Gmail fetch + classification + report generation + ambiguous review.
"""

import pandas as pd
import streamlit as st

from classifier import classify_email
from config import (
    INITIAL_EMAIL_FETCH_COUNT,
    MAX_EMAILS_PER_RUN,
    REVIEWABLE_CATEGORIES,
    SCAN_SIZE_OPTIONS,
)
from gmail_service import fetch_emails, get_gmail_service
from memory import learn_sender
from report import save_reports

st.set_page_config(page_title="Gmail Agent", page_icon="📧", layout="wide")

st.title("Gmail Cleanup AI Agent")
st.caption("Step 9: In-app ambiguous review and memory enrichment")

st.write("This step adds a review queue for ambiguous emails and learns approved classifications into memory.")

if "last_classified_emails" not in st.session_state:
    st.session_state["last_classified_emails"] = []

scan_size = st.selectbox(
    "Choose scan size",
    options=SCAN_SIZE_OPTIONS,
    index=SCAN_SIZE_OPTIONS.index(INITIAL_EMAIL_FETCH_COUNT),
)

st.caption(f"Current max allowed per run: {MAX_EMAILS_PER_RUN}")

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
st.subheader("Review Ambiguous Emails")

classified_emails = st.session_state.get("last_classified_emails", [])
ambiguous_items = [
    item for item in classified_emails
    if item["classification"].get("category") == "AMBIGUOUS"
]

if not ambiguous_items:
    st.info("No ambiguous emails to review in the current session.")
else:
    st.write(f"{len(ambiguous_items)} ambiguous emails need review.")

    for idx, item in enumerate(ambiguous_items):
        email = item["email"]

        with st.expander(f"Review email {idx + 1}: {email.get('subject', '(no subject)')}"):
            st.write(f"**Sender:** {email.get('sender', '')}")
            st.write(f"**Date:** {email.get('date', '')}")
            st.write(f"**Snippet:** {email.get('snippet', '')}")

            selected_category = st.selectbox(
                f"Choose category for email {idx + 1}",
                REVIEWABLE_CATEGORIES,
                key=f"category_{idx}",
            )

            memory_mode = st.radio(
                f"Learn using",
                options=["domain", "full_email"],
                index=0,
                horizontal=True,
                key=f"memory_mode_{idx}",
            )

            col1, col2 = st.columns(2)

            with col1:
                if st.button(f"Approve / Learn email {idx + 1}", key=f"approve_{idx}"):
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
                        "reason": f"Human-reviewed and learned into memory using key: {learned_key}",
                    }

                    st.success(
                        f"Saved to memory as '{learned_key}' → '{selected_category}'. "
                        f"This sender pattern should not need review again."
                    )

            with col2:
                if st.button(f"Reclassify only email {idx + 1}", key=f"reclassify_{idx}"):
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

            st.success("Reports regenerated after review.")

            st.subheader("Updated Detailed Report Preview")
            st.dataframe(detailed_df, use_container_width=True)

            st.subheader("Updated Summary Report")
            st.dataframe(summary_df, use_container_width=True)
        except Exception as exc:
            st.error(f"Error while regenerating reports: {exc}")