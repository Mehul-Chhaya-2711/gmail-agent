"""
Streamlit app for Gmail fetch + memory/rule classification + report generation.
"""

import pandas as pd
import streamlit as st

from classifier import classify_email
from config import INITIAL_EMAIL_FETCH_COUNT
from gmail_service import fetch_emails, get_gmail_service
from report import save_reports

st.set_page_config(page_title="Gmail Agent", page_icon="📧", layout="wide")

st.title("Gmail Cleanup AI Agent")
st.caption("Step 7: Classification with summary and detailed report generation")

st.write("This step fetches emails, classifies them, and saves summary and detailed reports.")

if st.button("Scan, Classify, and Generate Reports"):
    try:
        with st.spinner("Fetching, classifying, and generating reports..."):
            service = get_gmail_service()
            emails = fetch_emails(service, max_results=INITIAL_EMAIL_FETCH_COUNT)

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