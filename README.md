# Gmail Agent

A cloud-based Gmail Cleanup AI Agent built with Python, Streamlit, Gmail API, Gemini API, and GitHub Codespaces.

## Goal
Safely scan, classify, report on, and clean Gmail inbox data using:
1. Memory
2. Rules
3. LLM fallback

## Status
Step 1 complete: repository and cloud workspace initialized.

## Generate Gmail token.json using Colab

If Gmail OAuth is difficult inside GitHub Codespaces, use the Colab notebook below to generate `token.json` once, then upload it into the project root.

### Notebook
`notebooks/generate_gmail_token_colab.ipynb`

### How to use
1. Open the notebook in Google Colab from GitHub
2. Upload your `credentials.json`
3. Complete the Gmail OAuth flow
4. Download `token.json`
5. Upload `token.json` into the root of this project in Codespaces

### Important
- Never commit `credentials.json`
- Never commit `token.json`
- Both are already ignored in `.gitignore`