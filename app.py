"""
Temporary Streamlit app for Gmail fetch + memory/rule classification testing.
"""

import pandas as pd
import streamlit as st

from classifier import classify_email
from config import INITIAL_EMAIL_FETCH_COUNT
from gmail_service import fetch_emails, get_gmail_service

st.set_page_config(page_title="Gmail Agent", page_icon="📧", layout="wide")

st.title("Gmail Cleanup AI Agent")
st.caption("Step 6: Memory-first and rule-based classification")

st.write("This step fetches emails and classifies them using memory and rules.")

if st.button("Scan and Classify Emails"):
    try:
        with st.spinner("Fetching and classifying emails..."):
            service = get_gmail_service()
            emails = fetch_emails(service, max_results=INITIAL_EMAIL_FETCH_COUNT)

            enriched_rows = []
            for email in emails:
                result = classify_email(email)
                enriched_rows.append(
                    {
                        "email_id": email["email_id"],
                        "sender": email["sender"],
                        "subject": email["subject"],
                        "date": email["date"],
                        "category": result["category"],
                        "classification_source": result["classification_source"],
                        "confidence": result["confidence"],
                        "reason": result["reason"],
                    }
                )

        st.success(f"Fetched and classified {len(enriched_rows)} emails successfully.")

        if enriched_rows:
            df = pd.DataFrame(enriched_rows)
            st.dataframe(df, use_container_width=True)

            st.subheader("Category Counts")
            st.dataframe(
                df["category"].value_counts().rename_axis("category").reset_index(name="count"),
                use_container_width=True,
            )
        else:
            st.info("No emails found.")
    except Exception as exc:
        st.error(f"Error: {exc}")