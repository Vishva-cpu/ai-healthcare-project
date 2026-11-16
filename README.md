# AI Health Centre Project – Clinic Visit Sorter

**Student:** First-Year MSc Decision and Computing Science  
**Course:** CIT AI-Native Engineering Programme · Semester 1 · Assessment 5 (40%)  
**Domain:** Healthcare Decision Support & Triage Management  

---

## 1. Project Overview

At campus peak times, 10 or more students can arrive at the college health centre within 30 minutes. When seen strictly in arrival order (FIFO), an emergency patient (such as a student suffering acute chest pain, anaphylaxis, or uncontrolled bleeding) risks waiting behind multiple students requesting class attendance medical certificates.

The **Clinic Visit Sorter** is a console-based, safety-critical Python application that reads informal, multilingual student notes from `visits.csv` and organizes the triage queue into three distinct priority tiers:
1. `see_now`: Immediate attention required (chest pain, breathing trouble, fainting, heavy bleeding, facial swelling).
2. `today`: Same-day clinical examination (moderate fever, sprains, vomiting, burns).
3. `routine`: Non-urgent administrative visits (medical certificates, health checkups, old scabs).

### Core Medical Safety Invariant:
> **The tool is an organizing assistant, NOT a diagnostic engine.**  
> It **never diagnoses**, **never prescribes or gives advice**, and **never removes anyone from the queue**.  
> The human triage nurse examines every single student and retains 100% medical decision autonomy.

---

## 2. System Architecture & Safety Guardrails

The application employs a **Hybrid AI Architecture** pairing Groq LLM inference with deterministic Python post-processing guardrails:

```
[ visits.csv ] (English, Tamil, Tanglish)
      │
      ▼
[ load_visits() ] ──> Defensive CSV reader (handles unquoted commas)
      │
      ▼
[ classify() ]    ──> Groq LLM API (5-Role Prompt Framework: Authority, Exemplar, Constraint, Rubric, Metadata)
      │               ├── Schema validation (is_valid)
      │               └── Retry once; Fail-safe fallback to 'today' (Unknown is never routine)
      │
      ▼
[ raise_priority() ]  Deterministic Asymmetric Priority (Priority can only go UP to 'see_now')
      │               Scans bilingual red flags (nenju vali, moochu, mayakkam, ratham, swelling)
      │
      ▼
[ remove_diagnosis() ] Deterministic No-Diagnosis Rule (Regex scrubs disease names and guessing words)
      │
      ▼
[ write_reports() ]   Sorts: see_now > today > routine, then by arrival time
      ├── nurse_queue.csv  (Clinical Queue with original notes for nurse)
      └── summary.txt      (Administrative aggregate counts; zero student notes)
```

---

## 3. Directory Structure

```
├── visits.csv               # Input dataset (30 realistic notes across English, Tamil & Tanglish)
├── system_prompt.txt        # 5-Role System Prompt (Authority, Exemplar, Constraint, Rubric, Metadata)
├── test_single_note.py      # Checkpoint 2: Single-item end-to-end test script
├── main.py                  # Checkpoint 3: Complete triage application with 6 required functions
├── eval_harness.py          # Checkpoint 4: Automated 5-case eval harness + 3 red-team attack tests
├── nurse_queue.csv          # Output 1: Sorted clinical queue for triage nurse
├── summary.txt              # Output 2: Operational statistics report for clinic in-charge
├── SPECIFICATION.md         # Faculty Checkpoint 1 One-Page System Specification
├── JUDGMENT_FRAMEWORK.md    # Ethical evaluation, asymmetric risk analysis & human checkpoint
├── COST_AND_LATENCY.md      # Token utilization, empirical latency & daily cost projections
├── REFLECTION.md            # 400-word engineering reflection on responsible AI
├── AI_DECISION_JOURNAL.md   # Chronological log of development decisions and trade-offs
├── .env.example             # Template for API credentials
├── .gitignore               # Keeps secrets (.env) and caches out of GitHub
└── README.md                # Project documentation and viva preparation guide
```

---

## 4. Setup and Execution Guide

### Prerequisites
* Python 3.10+ installed.
* Groq API Key (free from [console.groq.com](https://console.groq.com/keys)).

### 1. Clone & Configure Environment
```bash
# Clone the repository
git clone <repo-url>
cd "AI clinic visitor sorter/AI PROJECT"

# Install dependencies
pip install groq python-dotenv

# Configure your environment variable
cp .env.example .env
# Edit .env and paste your Groq API key:
# GROQ_API_KEY=gsk_your_key_here
```

### 2. Run the Full Application (Checkpoint 3)
```bash
# Option A: Run in console mode
run.bat

# Option B: Launch the Interactive Dark-Themed Desktop GUI
gui.bat
```
* Generates `nurse_queue.csv` and `summary.txt`.

### 3. Run Automated Evaluation & Red-Team Suite (Checkpoint 4)
```bash
python eval_harness.py
```
* Evaluates 5 ground-truth benchmark cases.
* Runs 3 adversarial red-team attacks:
  1. Priority tampering attempt (requesting `routine` while having crushing chest pain).
  2. Diagnostic baiting & prescription attempt.
  3. Tamil/Tanglish emergency red flag.

---

## 5. Summary of Empirical Results

### Evaluation Benchmark Results:
* **Category Classification Accuracy:** **100% (5/5)**
* **Priority Classification Accuracy:** **100% (5/5)**
* **Red-Team Defense Rate:** **100% (3/3 attacks successfully mitigated)**
* **Average Request Latency:** **304.5 ms (~0.30 s)** on Groq (`qwen/qwen3.8-27b`)
* **Projected Operational Cost:** **$0.0055/day** (~₹0.46/day) for 100 daily clinic visits.

---

## 6. Viva Q&A Quick Reference Guide (For Presentation)

During your evaluation, faculty will ask line-by-line questions. Here are the exact answers:

* **Q: Why does Python have an asymmetric priority rule (`raise_priority`)?**
  * *Answer:* In clinical triage, false negatives (classifying an emergency as routine) can be fatal, whereas false positives only cost a 60-second nurse check. Therefore, priority can only go UP to `see_now`, never down.
* **Q: What happens if the Groq API goes down or returns malformed JSON?**
  * *Answer:* The system retries once. If both attempts fail, the fail-safe rule triggers: **"Unknown is never routine"**. The record defaults to priority `today` and category `other`, and is still screened through our local Python red-flag dictionary.
* **Q: Why are there two separate output files (`nurse_queue.csv` and `summary.txt`)?**
  * *Answer:* Privacy separation. The nurse needs student notes to provide medical care (`nurse_queue.csv`). The administrative in-charge only needs aggregate operational counts (`summary.txt`), so student notes and IDs are strictly excluded.
* **Q: How does the system handle students writing in Tanglish?**
  * *Answer:* The system prompt incorporates cultural metadata defining Tanglish terms (*nenju vali*, *moochu*, *mayakkam*, *ratham*), and Python's deterministic red-flag list contains regex triggers for these keywords to catch critical cases even if the LLM wavers.

