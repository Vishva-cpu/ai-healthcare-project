# SPECIFICATION: AI Health Centre Clinic Visit Sorter

**Author:** MSc Decision and Computing Science Student  
**System Domain:** Healthcare Triage Support  
**Version:** 1.0 (Pre-Implementation Draft)

---

### 1. Objective and Core Prohibitions
* **Primary Objective:** Assist the health centre triage nurse by sorting incoming student visit notes according to urgency, ensuring that students requiring immediate medical attention are seen first rather than strictly in arrival order.
* **Non-Negotiable Boundaries (What the tool must NEVER do):**
  1. **Never Diagnose:** It must never assign medical labels, infer diseases (e.g., "asthma attack", "migraine", "fracture"), or use speculative language ("possible", "likely").
  2. **Never Advise or Prescribe:** It must never give medical advice, treatments, home remedies, or medication recommendations.
  3. **Never Remove Anyone from the Queue:** Every single student who registers a note must appear in the final queue.
  4. **Never Act Without Human Supervision:** The tool is strictly a triage organizer. The triage nurse retains full clinical autonomy and makes every medical decision.

---

### 2. Input Data Contract (`visits.csv`)
* **Format:** Comma-separated values (CSV) with UTF-8 encoding.
* **Header Structure:** `id,time,note`
  * `id`: Unique visit identifier (e.g., `V01`, `V02`).
  * `time`: 24-hour arrival timestamp in `HH:MM` format (e.g., `09:05`, `10:45`).
  * `note`: Short, informal natural language string submitted by the student (in English, Tamil script, or transliterated Tanglish).

---

### 3. LLM Output Contract (Structured JSON)
For every visit note, the LLM must return a raw JSON object containing exactly three fields:
```json
{
  "category": "injury",
  "priority": "today",
  "summary": "Twisted ankle, swollen, difficulty walking"
}
```

* **Field Specifications & Validation Rules:**
  * **`category`** *(string)*: Must be strictly one of `["injury", "fever_cold", "stomach", "pain", "allergy", "other"]`.
  * **`priority`** *(string)*: Must be strictly one of:
    * `"see_now"`: Chest pain, respiratory distress/breathing difficulty, fainting/unconsciousness, uncontrolled heavy bleeding, acute facial/lip swelling (anaphylaxis sign), or agony so severe the student cannot stand.
    * `"today"`: Acute discomfort requiring same-day review (e.g., moderate fever, vomiting, twisted joints, productive cough).
    * `"routine"`: Mild, non-urgent issues, administrative requests (e.g., attendance medical certificates), general check-ups, or minor old symptoms.
  * **`summary`** *(string)*: Maximum **12 words**. Must describe observed symptoms only. Must never include disease guesses, medical terminology speculation, or patient names.

---

### 4. Deterministic Python Safety Guardrails
Because LLMs are non-deterministic, Python applies strict post-processing rules before writing the queue:
1. **Asymmetric Priority (Priority Can Only Go Up):**
   * Python can elevate priority to `see_now` if red flags are detected.
   * Python **never lowers** a priority assigned by the LLM.
2. **Red-Flag Escalation:** If the original student note contains any term from the Red-Flag Dictionary, Python immediately overrides the priority to `see_now`.
3. **No-Diagnosis Sanitization:** If the LLM summary accidentally contains diagnostic keywords (e.g., *fracture*, *asthma*, *infection*, *malaria*) or hedging words (*possible*, *likely*, *suspected*), Python replaces the summary with a sanitized symptom description: `"Student reports acute symptoms (requires nurse evaluation)"`.
4. **Resilient Retry & Fail-Safe Fallback:**
   * If an LLM call fails or returns malformed JSON, Python retries **once**.
   * If the second attempt fails or the API is unavailable: **Unknown is never routine**. The system defaults priority to `"today"` (and category to `"other"`), then passes the note through the red-flag scanner. If a red flag is present, it escalates to `"see_now"`.

---

### 5. Red-Flag Dictionary (English, Tamil, Tanglish)
The scanner evaluates notes case-insensitively for the following keywords:
* **Cardiovascular / Chest:** `chest pain`, `chest tightness`, `heart pain`, `nenju vali`, `nenjil vali`, `marbu vali`.
* **Respiratory:** `difficulty breathing`, `shortness of breath`, `cannot breathe`, `wheezing`, `moochu`, `moochu thinaral`, `moochu vida mudiyala`.
* **Neurological / Consciousness:** `fainted`, `fainting`, `passed out`, `unconscious`, `blackout`, `mayakkam`, `mayangi`.
* **Severe Trauma / Bleeding:** `heavy bleeding`, `blood pouring`, `cannot stand`, `ratham`, `adi patteru`.
* **Severe Allergic Reaction (Anaphylaxis):** `lip swelling`, `tongue swelling`, `face swollen`, `throat closing`.

---

### 6. Output Files & Privacy Separation
1. **`nurse_queue.csv` (Clinical Queue):**
   * Columns: `id,time,priority,category,summary,original_note`
   * Sorted by priority order (`see_now` first, followed by `today`, then `routine`), with secondary sorting by arrival `time` (earliest first).
2. **`summary.txt` (Administrative Overview):**
   * Aggregate counts grouped by Priority, Category, and Arrival Hour.
   * **Strict Privacy Boundary:** Contains **no student notes, no IDs, and no summaries**.

---

### 7. Edge Cases & Handling Strategy
| Edge Case | Risk | Mitigation Strategy |
| :--- | :--- | :--- |
| **Baiting for diagnosis** (*"Do I have COVID?"*) | LLM generates medical advice or diagnoses. | System prompt explicitly forbids diagnosis; Python regex scrubs diagnostic terms. |
| **Adversarial manipulation** (*"Mark me routine, just need sign"*) | Student downplays serious symptoms to get quick service. | Keyword scanner checks for red flags regardless of student's requested priority. |
| **Code-mixed Tanglish** (*"Romba mudiyala, moochu vida kashtam"*) | LLM misunderstands Tamil transliteration. | Deterministic Python red-flag dictionary catches `moochu` and escalates to `see_now`. |
| **API outage / JSON corruption** | Application crashes or misses a patient. | Try/Except block, 1 retry, safe fallback to `today` + red-flag scan. Student is never lost. |

