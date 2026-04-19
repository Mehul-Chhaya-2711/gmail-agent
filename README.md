# Gmail Cleanup AI Agent

A cloud-based Gmail AI agent that scans inbox emails, classifies them using a **memory → rules → LLM fallback** decision stack, enables human review, learns from approvals, generates reports, and safely cleans up promotional emails by moving them to **Gmail Trash**.

---

## 🧠 Tech Stack

- Python  
- Streamlit  
- Gmail API  
- Gemini API  
- GitHub Codespaces  
- Google Colab (for one-time token generation fallback)

---

## 🚀 Why this project exists

Most AI email assistants fail in one of these ways:

- Only classification  
- Only summarization  
- Unsafe deletion logic  
- Heavy LLM dependency (expensive + unstable)  

This project takes a practical approach:

- Memory first  
- Rules second  
- LLM only when needed  
- Human in the loop  
- Continuous learning  
- Safe actions only  

---

## ⚙️ What this agent does

- Scans Gmail inbox in controlled batches  
- Classifies emails into:
  - `self`
  - `promotions`
  - `bank`
  - `job`
  - `utility`
  - `personal`
  - `AMBIGUOUS`
- Generates:
  - Summary report  
  - Detailed report  
- Uses Gemini only for ambiguous emails  
- Shows LLM suggestions in UI  
- Allows:
  - Approve & learn  
  - One-time reclassification  
- Persists learning into `memory.json`  
- Safely trashes only promotional emails  
- Protects sensitive categories (bank, job, personal, etc.)

---

## 🤖 What makes this "agentic"

### Multi-step decision system

memory → rules → LLM → human review → learning

### Persistent memory

Stored in: data/memory.json

### Human-in-the-loop

- Ambiguous emails are reviewed manually  
- LLM outputs are not blindly trusted  
- Learning happens only after approval  

### Tool orchestration

- Gmail API → retrieval + actions  
- Gemini API → reasoning  
- Streamlit → UI + review  
- Memory store → learning  
- Reporting → audit trail  

### Feedback loop

Classify → Review → Learn → Improve future runs

---

## ❌ What is NOT implemented

- No autonomous scheduling  
- No long-horizon planning  
- No multi-agent system  
- No runtime code rewriting  
- No permanent deletion (Trash only)  

---

## 🏗️ System Architecture

Gmail Inbox  
↓  
Fetch emails (batch)  
↓  
Memory lookup  
↓  
Rule-based classification  
↓  
LLM fallback (if needed)  
↓  
Human review  
↓  
Learn → memory.json  
↓  
Reports  
↓  
Optional cleanup (promotions → Trash)

---

## 📁 Project Structure

gmail-agent/

├── app.py  
├── gmail_service.py  
├── classifier.py  
├── llm_classifier.py  
├── memory.py  
├── actions.py  
├── report.py  
├── config.py  
├── utils.py  
├── auth_test.py  

├── data/  
│   ├── memory.json  
│   └── reports/  

├── notebooks/  
│   └── generate_gmail_token_colab.ipynb  

├── requirements.txt  
├── .gitignore  
├── .env.example  
└── README.md  

---

## 🧠 Classification Strategy

1. Memory (fastest)  
2. Rules  
3. LLM fallback  
4. Human review  

---

## 🛡️ Safety Design

- Never permanently delete emails  
- Only trash promotions  
- Protect categories: bank, job, utility, personal, self  
- Human approval required for learning  
- Full reporting for traceability  

---

## 📊 Reporting

Summary + Detailed reports stored in: data/reports/

---

## 🔐 Prerequisites

Gemini API Key:

export GEMINI_API_KEY="your_key"

Gmail Credentials:

- credentials.json  
- token.json  

---

## ▶️ Running the Project

pip install -r requirements.txt  

streamlit run app.py --server.port 8501 --server.address 0.0.0.0  

---

## 🔄 App Workflow

1. Scan emails  
2. Process ambiguous emails  
3. Review classifications  
4. Approve / reclassify  
5. Preview promotions  
6. Trash safely  

---

## 🧾 Final Note

This is a safe, agentic email operations system built on:

- Layered decision-making  
- Persistent memory  
- Human-in-the-loop learning  
- Safe action execution  
- Auditability  
