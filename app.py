"""
Temporary Streamlit app for Gmail authentication and safe email fetch testing.
"""

import streamlit as st
import pandas as pd

from gmail_service import get_gmail_service, fetch_emails
from config import INITIAL_EMAIL_FETCH_COUNT

st.set_page_config(page_title="Gmail Agent", page_icon="📧", layout="wide")

st.title("Gmail Cleanup AI Agent")
st.caption("Step 4: Streamlit verification with Gmail fetch")

st.write("This step checks that the cloud app can fetch a safe batch of emails.")

if st.button("Authenticate and Fetch Emails"):
    try:
        with st.spinner("Connecting to Gmail..."):
            service = get_gmail_service()
            emails = fetch_emails(service, max_results=INITIAL_EMAIL_FETCH_COUNT)

        st.success(f"Fetched {len(emails)} emails successfully.")

        if emails:
            df = pd.DataFrame(emails)[["email_id", "sender", "subject", "date", "snippet"]]
            st.dataframe(df, use_container_width=True)
        else:
            st.info("No emails found.")
    except Exception as exc:
        st.error(f"Error: {exc}")