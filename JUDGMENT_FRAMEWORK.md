# Judgment Framework: AI Clinic Visit Sorter

**Module:** CIT AI-Native Engineering Programme · Assessment 5  
**Domain:** Healthcare Triage Support  
**Human Checkpoint Authority:** The Triage Nurse

---

## 1. The Core Philosophy of Asymmetric Risk in Healthcare Triage

In classical computer science, an error is symmetric: predicting Class A instead of Class B is evaluated with the same loss penalty as predicting Class B instead of Class A.

In **clinical triage engineering**, errors are **deeply asymmetric**:

$$\text{Cost}(\text{False Negative}) \gg \text{Cost}(\text{False Positive})$$

* **False Negative (Assigning a priority that is too low):**
  * *Example:* A student with early myocardial infarction or acute anaphylaxis is assigned `routine` or `today`.
  * *Consequence:* The student is forced to wait behind non-urgent visitors. Their physiological condition deteriorates rapidly in the waiting area, potentially causing permanent injury or fatality. **This is a catastrophic failure mode.**
* **False Positive (Assigning a priority that is too high):**
  * *Example:* A student with a mild tension headache or non-urgent anxiety is prioritized as `see_now`.
  * *Consequence:* The triage nurse evaluates the student in 60 seconds, discovers they are hemodynamically stable, and directs them to the regular waiting room. The only consequence is a brief minor delay to the clinic queue.

> **Engineering Principle:** The system is intentionally architected to be risk-averse. When uncertainty exists, the priority **must always escalate upward, never downward**.

---

## 2. Component-by-Component Judgment Framework Table

| Component | 1. Purpose & Automated Boundary | 2. Failure Mode & Consequence | 3. Human Checkpoint & Mitigation Guardrail |
| :--- | :--- | :--- | :--- |
| **Data Ingestion (`load_visits`)** | Ingests raw CSV visit records containing informal, unstructured student notes. | Natural language notes contain unquoted commas, truncating symptom descriptions. | **Mitigation:** Defensive comma re-joining (`",".join(row[2:])`) prevents truncated symptom loss. |
| **LLM Classification (`classify`)** | Generates structured JSON mapping informal notes into standardized categories and urgency levels. | Non-deterministic schema violations, network dropouts, or API outages. | **Mitigation:** Strict schema validator (`is_valid`), automated 1-retry, and fail-safe fallback to `today`. Unknown is never routine. |
| **Asymmetric Escalation (`raise_priority`)** | Scans notes for bilingual red flags (*nenju vali*, *moochu*, *ratham*, *swelling*, *bleeding*). | LLM misinterprets colloquial Tanglish slang and assigns lower priority. | **Mitigation:** Python deterministic override. Priority can only go UP to `see_now`, never down. |
| **Diagnosis Scrubbing (`remove_diagnosis`)** | Enforces the non-diagnostic boundary by stripping medical labels and guessing words. | LLM hallucinates medical diagnosis (*"likely appendicitis"*) or suggests medications. | **Mitigation:** Regex keyword scrubber replaces speculative text with neutral symptom statements. |
| **Queue Organization (`write_reports`)** | Sorts records into `see_now` > `today` > `routine`, secondary-sorted by arrival time. | Queue inversion causing an emergency patient to wait behind an administrative visitor. | **Human Checkpoint:** The triage nurse reviews every entry in `nurse_queue.csv`, visually verifies patient state, and retains total medical decision autonomy. |
| **Administrative Reporting (`summary.txt`)** | Aggregates volume by priority, category, and arrival hour for clinic management. | Accidental data leakage of student personal medical complaints to non-clinical staff. | **Mitigation:** Strict privacy wall. `summary.txt` contains zero notes, zero names, and zero patient IDs. |

---

## 3. The Indispensable Human Checkpoint

The AI Clinic Visit Sorter is an **organizing tool, never a clinical decision-maker**:

1. **Every Student is Examined:** The tool has no mechanism to discharge, dismiss, or delete a student from the register.
2. **Nurse Retains Total Authority:** The nurse can immediately alter the queue order upon visual observation in the waiting lobby.
3. **No Closed-Loop Prescriptions:** The software never generates advice, treatment regimens, or medical conclusions.
4. **Accountability:** The licensed healthcare professional remains solely responsible for all diagnostic and therapeutic actions.

