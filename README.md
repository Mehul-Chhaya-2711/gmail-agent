Use this as your README.md.

# Gmail Cleanup AI Agent

A cloud-based Gmail AI agent that scans inbox emails, classifies them using a **memory → rules → LLM fallback** decision stack, lets a human review uncertain cases inside the app, learns from approvals, generates reports, and safely cleans up promotional emails by moving them to **Gmail Trash**.

Built with:
- Python
- Streamlit
- Gmail API
- Gemini API
- GitHub Codespaces
- Google Colab (for one-time token generation fallback)

---

## Why this project exists

Most “AI email assistants” stop at one of these:
- classification only
- summarization only
- deletion without enough guardrails
- LLM-heavy designs that become expensive and unstable

This project takes a more practical route:
- use **memory first**
- use **rules second**
- use the **LLM only when needed**
- keep a **human in the loop**
- learn from review over time
- apply **safe actions only**

That makes it cheaper, more explainable, and much safer for real inbox cleanup.

---

## What this agent does

The agent can:

- scan emails from Gmail in controlled batches
- classify emails into categories such as:
  - `self`
  - `promotions`
  - `bank`
  - `job`
  - `utility`
  - `personal`
  - `AMBIGUOUS`
- generate:
  - a **summary report**
  - a **detailed report**
- send only ambiguous emails to Gemini
- show LLM suggestions in the UI
- let the user:
  - approve and learn
  - reclassify only for one email
- persist approved patterns into `memory.json`
- safely trash promotional emails only
- avoid touching protected categories such as bank, job, personal, utility, and self

---

## What makes this “agentic”

This project is not just a script calling an LLM. It has several agentic behaviors.

### Agentic patterns applied here

#### 1. Multi-step decision making
The system does not jump directly to the LLM.

It reasons in layers:
1. memory
2. rules
3. LLM fallback
4. human review
5. learning back into memory

That is a real decision workflow, not a single inference call.

#### 2. State and memory
The agent keeps persistent memory in:

data/memory.json

This lets it improve over time. Once a sender or sender domain is learned, future similar emails can bypass the LLM entirely.

#### 3. Human-in-the-loop

The app does not auto-trust every uncertain LLM answer.

Instead:

ambiguous or LLM-classified emails are surfaced in the UI
the user approves or reclassifies
approved knowledge is persisted

This is a strong agentic pattern for safety-critical automation.

#### 4. Tool use

The agent coordinates multiple tools/services:

Gmail API for retrieval and safe trashing
Gemini API for fallback reasoning
Streamlit for human review
local memory store for learning
reporting layer for auditability

#### 5. Feedback loop

The system closes the loop:

classify
review
learn
reduce future ambiguity
reduce future LLM usage

This is one of the most important “agentic” characteristics in the project.

What is not applied here

This is also important.

1. No autonomous background execution

The agent does not currently run on a schedule by itself.

It is user-triggered through Streamlit.

2. No long-horizon planning

The agent does not decompose goals into dynamic subgoals or plan across many steps by itself.

Its orchestration is structured and deterministic.

3. No multi-agent architecture

There are not multiple cooperating agents with separate roles.

This is a single-agent workflow with modular components.

4. No runtime code rewriting

The agent does not edit Python source files to “learn.”

Learning is safely stored in:

data/memory.json

That is intentional. It is safer, more auditable, and easier to control.

5. No permanent deletion

The system does not permanently delete emails.

Cleanup action uses:

Gmail Trash only

This is a deliberate safety design.

System architecture
High-level flow
Gmail Inbox
   ↓
Fetch emails in controlled batch
   ↓
Memory lookup
   ↓
Rule-based classification
   ↓
If still ambiguous → Gemini fallback
   ↓
Human review in app
   ↓
Approved learning → memory.json
   ↓
Generate reports
   ↓
Optional safe trashing of promotions
Project structure
gmail-agent/
│
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
│
├── data/
│   ├── memory.json
│   └── reports/
│
├── notebooks/
│   └── generate_gmail_token_colab.ipynb
│
├── requirements.txt
├── .gitignore
├── .env.example
└── README.md
How each file works
app.py

This is the main Streamlit application.

It:

renders the UI
triggers scanning
triggers Gemini processing
shows review sections
updates reports
previews deletable promotions
triggers safe trashing

This is the orchestration layer.

gmail_service.py

This file handles Gmail connectivity.

It:

loads OAuth credentials from credentials.json and token.json
refreshes tokens when needed
creates the Gmail API client
fetches emails page by page
normalizes sender, subject, date, snippet, and body

This is the Gmail access layer.

classifier.py

This file handles non-LLM classification.

It applies the primary decision hierarchy:

memory lookup
self-email check
keyword/rule classification
fallback to AMBIGUOUS

This is the fast, cheap classification layer.

llm_classifier.py

This file handles Gemini fallback only for unresolved emails.

It:

builds the prompt
constrains output to JSON
rate-limits requests
respects a hard per-run cap
updates only ambiguous items

This is the probabilistic reasoning layer.

memory.py

This file handles persistent learning.

It:

loads memory from data/memory.json
saves new learned mappings
extracts sender email/domain
matches incoming senders to learned patterns
writes new patterns after human approval

This is the agent’s durable memory layer.

actions.py

This file handles safe Gmail actions.

It:

identifies deletable emails
restricts cleanup to promotions
moves those emails to Gmail Trash
avoids permanent deletion

This is the action execution layer.

report.py

This file builds reports.

It:

creates the detailed report row-by-row
creates summary metrics
saves:
detailed_report.csv
detailed_report.xlsx
summary_report.csv

This is the audit and reporting layer.

config.py

This centralizes all important settings:

scan sizes
max emails per run
max LLM emails per run
Gemini model name
safety categories
file paths
report paths

This is the configuration layer.

utils.py

This contains helper utilities such as:

safe JSON extraction/parsing from Gemini output

This is the utility layer.

auth_test.py

This is a lightweight credential validation script.

It is useful to confirm Gmail authentication works before running the full app.

Classification strategy

The classification logic is intentionally layered.

1. Memory

If sender or sender domain has already been learned, memory wins first.

Example:

{
  "audible.in": "promotions",
  "indeed.com": "job"
}

This is fastest and cheapest.

2. Rules

If memory does not match, the classifier uses keywords.

Examples:

bank terms → bank
recruiter/job terms → job
bill/payment terms → utility
deals/discount/coupon → promotions

This is deterministic and explainable.

3. LLM fallback

Only if the email remains unresolved:

classify as AMBIGUOUS
then optionally send to Gemini

Gemini is never the first resort.

4. Human review

LLM suggestions are not silently trusted for durable learning.

The user can:

approve and learn
reclassify only for one email

Only approved learning updates memory.json.

Why memory comes before the LLM

This is one of the most important design choices.

Benefits:

fewer API calls
lower cost
lower latency
more deterministic behavior
less repeat work
explainable classification path

This turns the LLM into a fallback, not the core engine.

Safety design

This project is built around defensive automation.

Safety rules applied
never permanently delete emails
only trash promotions
protect categories:
bank
job
utility
personal
self
review ambiguous/LLM-suggested emails in the app
persist learned decisions only after approval
keep reporting for traceability
Current cleanup policy

Only these are eligible for cleanup:

emails classified as promotions

Cleanup action:

trash, not permanent delete
Reporting

The project generates two reports.

1. Summary report

Includes:

total emails scanned
category counts
ambiguous count
LLM processed count
rule-based count
memory-based count
manual review count
deleted emails count
before vs after email count
2. Detailed report

Includes one row per email:

email_id
sender
subject
date
category
classification_source
confidence
action
reason

Reports are saved to:

data/reports/
Prerequisites

Before running the project, you need 2 external credentials:

1. Gemini API key

Used for LLM fallback classification.

2. Gmail OAuth credentials

Used for Gmail API access.

These are not included in the repository.

Setup requirements
A. Gemini setup

Create a Gemini API key and set it as an environment variable.

Example:

export GEMINI_API_KEY="your_gemini_api_key_here"

A template file is provided:

.env.example
B. Gmail setup

You need:

credentials.json
token.json
credentials.json

Create a Google Cloud OAuth Desktop App client and download the JSON.

token.json

Generate it using the provided Colab notebook:

notebooks/generate_gmail_token_colab.ipynb

Then upload both files into the project root locally in Codespaces, not into Git.

Security note

These files must never be committed:

credentials.json
token.json

They are ignored by .gitignore.

Running the project
Install dependencies
pip install -r requirements.txt
Start the app
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

Open the forwarded Codespaces port in your browser.

Typical workflow in the app
1. Scan emails

Choose a batch size and click:

Scan Emails
2. Process ambiguous emails

Click:

Process Ambiguous

This sends unresolved emails to Gemini, within configured limits.

3. Review suggested categories

For LLM or ambiguous emails:

approve and learn
or reclassify only
4. Preview promotional cleanup

Review emails eligible for safe cleanup.

5. Trash promotions safely

Click:

Delete Promotions Safely

That moves promotional emails to Gmail Trash.

Command input: what it is right now

The command input in the UI is currently a lightweight shortcut layer.

At present, it is mostly:

a UX affordance
a future extension point

It can recognize phrases like:

show marketing emails
clean inbox safely
scan 100 emails

But the primary execution still happens through buttons for safety and predictability.

This was intentional during development.

Design tradeoffs
Why not let the LLM classify everything?

Because that would:

increase cost
reduce determinism
slow down the system
make debugging harder
Why not auto-learn every Gemini answer?

Because some classifications require human judgment.

The system only writes durable knowledge after explicit approval.

Why not modify Python rule code dynamically?

Because dynamic code rewriting is fragile and risky.

Learning goes into memory.json, which is safer and easier to audit.

Why Trash instead of delete?

Because inbox cleanup must be reversible.

This project optimizes for safe automation, not aggressive automation.

Limitations

Current limitations include:

no background scheduler yet
no multi-user auth management
no server-side credential vault
command input is not yet a full orchestration engine
Gmail OAuth setup is still a one-time manual step
Gemini free-tier quotas can block ambiguous processing on some days

These are known tradeoffs, not accidental omissions.

Future improvements

Possible next upgrades:

background scheduled runs
full command input execution engine
sender/domain suggestion quality improvements
smarter domain extraction
dashboard charts and trends
bulk review workflow
deployment outside Codespaces
better credential onboarding
rule suggestion generation from reviewed examples
Why this project is useful

This project demonstrates how to build an AI system that is:

practical
cost-aware
reviewable
safe
incrementally self-improving

It is not “AI for the sake of AI.”
It uses the LLM only where the deterministic layers stop being enough.

That is the core philosophy behind the design.

Repo hygiene and security

This repository is designed to be public-safe.

It excludes:

Gmail OAuth secrets
token files
runtime secret files

Recommended practice:

rotate keys if exposure is suspected
do not commit runtime credentials
keep notebook outputs cleared before sharing
Quick demo script

If you are demoing this project:

Start app in Codespaces
Scan 50 emails
Show category distribution
Process ambiguous emails with Gemini
Approve one or two learned mappings
Re-scan and show reduced ambiguity
Preview promotional emails
Safely trash promotions
Show updated report

That demonstrates:

agentic loop
cost control
human oversight
safe actioning
continual improvement
Final note

This project is best understood as a safe, agentic email operations system rather than a simple classifier.

Its core strengths are:

layered decision making
persistent memory
human-in-the-loop learning
cautious action execution
auditability through reports

If you use, fork, or extend it, keep those principles intact.


If you want, I can also give you:
- a **shorter, GitHub-polished version**
- a **LinkedIn project description**
- a **repo tagline + About section**
- a **demo walkthrough script**