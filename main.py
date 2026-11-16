"""
AI Health Centre Project - Clinic Visit Sorter
CIT AI-Native Engineering Programme - Semester 1 - Assessment 5

Main application module implementing the 6 required functions:
1. load_visits(filepath)
2. is_valid(data)
3. classify(client, note, system_prompt)
4. raise_priority(note, current_priority)
5. remove_diagnosis(summary)
6. write_reports(processed_records)
"""

import csv
import json
import os
import re
from datetime import datetime
from dotenv import load_dotenv
from groq import Groq

# Allowed schema values as defined by the Faculty Specification
ALLOWED_CATEGORIES = {"injury", "fever_cold", "stomach", "pain", "allergy", "other"}
ALLOWED_PRIORITIES = {"see_now", "today", "routine"}

# Priority rank mapping: lower number = higher urgency
PRIORITY_RANK = {"see_now": 0, "today": 1, "routine": 2}

# Bilingual Red-Flag vocabulary (English, Tamil script, Tanglish transliteration)
RED_FLAGS = [
    # Cardiovascular & Chest symptoms
    "chest pain", "chest tightness", "heart pain", "nenju vali", "nenjil vali", "marbu vali",
    # Respiratory distress
    "difficulty breathing", "shortness of breath", "cannot breathe", "breathless", 
    "wheezing", "moochu", "moochu thinaral", "moochu vida mudiyala", "choking",
    # Neurological / Consciousness
    "faint", "fainted", "fainting", "passed out", "unconscious", "blackout", "mayakkam", "mayangi",
    # Severe Trauma / Bleeding / Inability to stand
    "heavy bleeding", "blood soaking", "cannot stop bleeding", "cannot stand", "can't stand",
    "ratham", "adi patteru", "severe bleeding",
    # Anaphylaxis (Severe allergic reaction)
    "lip swelling", "lips are swelling", "tongue swelling", "face swollen", "throat closing", "throat feels tight"
]

# Prohibited diagnostic labels and speculative terms (Rule 2: No Diagnosis)
BANNED_DIAGNOSES = [
    "malaria", "typhoid", "dengue", "jaundice", "covid", "covid-19",
    "asthma", "pneumonia", "bronchitis", "migraine", "fracture",
    "food poisoning", "appendicitis", "heart attack", "angina",
    "possible", "likely", "suspected", "diagnosed", "probable"
]


def load_visits(filepath):
    """
    Reads the visits CSV file and returns a list of visit dictionaries.
    Each item contains 'id', 'time', and 'note'.
    Handles commas safely even if notes are unquoted in the CSV.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found at: {filepath}")
    
    visits = []
    with open(filepath, mode="r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader, None)  # Skip header
        for row in reader:
            if not row or len(row) < 3:
                continue
            v_id = row[0].strip()
            v_time = row[1].strip()
            # If the note contained commas and wasn't quoted, join the remaining tokens
            v_note = ",".join(row[2:]).strip()
            visits.append({
                "id": v_id,
                "time": v_time,
                "note": v_note
            })
    return visits


def is_valid(data):
    """
    Validates whether the dictionary returned by the LLM strictly matches
    all faculty requirements:
    1. Must be a dict with keys 'category', 'priority', 'summary'
    2. 'category' must be in ALLOWED_CATEGORIES
    3. 'priority' must be in ALLOWED_PRIORITIES
    4. 'summary' must be a non-empty string with 12 words or fewer
    """
    if not isinstance(data, dict):
        return False
    
    # Check all required keys exist
    if not all(k in data for k in ("category", "priority", "summary")):
        return False
    
    category = data.get("category")
    priority = data.get("priority")
    summary = data.get("summary")
    
    if category not in ALLOWED_CATEGORIES:
        return False
    
    if priority not in ALLOWED_PRIORITIES:
        return False
    
    if not isinstance(summary, str) or not summary.strip():
        return False
    
    # Word count check: must be 12 words or fewer
    word_count = len(summary.strip().split())
    if word_count > 12:
        return False
    
    return True


# Active primary model and secondary failover model
PRIMARY_MODEL = "openai/gpt-oss-20b"
BACKUP_MODEL = "qwen/qwen3.8-27b"


def classify(client, note, system_prompt):
    """
    Calls the Groq LLM API to classify a student note.
    Implements retry, failover, and fallback rules:
    - Attempts classification with PRIMARY_MODEL.
    - If rate limited (429) or error occurs, fails over to BACKUP_MODEL.
    - Retries once if the first attempt fails or produces invalid JSON.
    - If both attempts fail: falls back to priority 'today' and category 'other'.
      (Unknown is never routine).
    """
    fallback_result = {
        "category": "other",
        "priority": "today",
        "summary": "Pending nurse review"
    }
    
    models_to_try = [PRIMARY_MODEL, BACKUP_MODEL]
    
    for attempt, model_name in enumerate(models_to_try):
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Student Visit Note: \"{note}\""}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            raw_text = response.choices[0].message.content.strip()
            parsed = json.loads(raw_text)
            
            if is_valid(parsed):
                return parsed
            else:
                print(f"    [Warning] Attempt {attempt + 1} ({model_name}): LLM response failed validation schema.")
        except Exception as e:
            print(f"    [Warning] Attempt {attempt + 1} ({model_name}) API error: {e}")
            
    # If both models/attempts failed, return safe fallback
    print("    [Fallback Triggered] LLM call failed twice. Defaulting to priority 'today'.")
    return fallback_result


def raise_priority(note, current_priority):
    """
    Python Safety Rule 1: Priority can ONLY go up.
    Scans the original student note for critical red flags (in English, Tamil, Tanglish).
    If a red flag is found (and not explicitly negated like 'no chest pain'),
    escalates priority to 'see_now'.
    Python NEVER lowers a priority.
    """
    note_lower = note.lower()
    
    # Common negation patterns (e.g., 'no chest pain', 'no breathing trouble')
    negations = [
        "no chest pain", "no fever or chest pain", "without chest pain",
        "no breathing trouble", "no difficulty breathing"
    ]
    
    # Temporarily mask negated phrases to avoid false positive escalation
    cleaned_note = note_lower
    for neg in negations:
        cleaned_note = cleaned_note.replace(neg, "")

    for flag in RED_FLAGS:
        if flag in cleaned_note:
            return "see_now"
    
    # Python never lowers a priority
    return current_priority


def remove_diagnosis(summary):
    """
    Python Safety Rule 2: No diagnosis.
    If the summary contains disease names, diagnostic conclusions, or speculative words
    (e.g., 'possible', 'likely'), replaces the summary with a neutral symptom statement.
    """
    summary_lower = summary.lower()
    for banned in BANNED_DIAGNOSES:
        pattern = r"\b" + re.escape(banned) + r"\b"
        if re.search(pattern, summary_lower):
            # Scrubbed neutral summary strictly describing symptoms without diagnosis
            return "Symptom evaluation requested"
    return summary


def write_reports(processed_records, queue_output_path="nurse_queue.csv", summary_output_path="summary.txt"):
    """
    Generates the two required output files:
    1. nurse_queue.csv:
       - Sorted primarily by urgency (see_now > today > routine), then by arrival time.
       - Contains id, time, priority, category, summary, original_note.
    2. summary.txt:
       - Aggregate statistics for health centre in-charge: counts by priority, category, and hour.
       - Strict privacy requirement: NO student notes, names, or IDs.
    """
    # 1. Sort records: primary key = priority rank, secondary key = arrival time
    sorted_records = sorted(
        processed_records,
        key=lambda r: (PRIORITY_RANK.get(r["priority"], 3), r["time"])
    )
    
    # 2. Write nurse_queue.csv
    fieldnames = ["id", "time", "priority", "category", "summary", "original_note"]
    with open(queue_output_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in sorted_records:
            writer.writerow({
                "id": r["id"],
                "time": r["time"],
                "priority": r["priority"],
                "category": r["category"],
                "summary": r["summary"],
                "original_note": r["original_note"]
            })
    print(f"[Output] Successfully generated: {queue_output_path}")

    # 3. Compute statistics for summary.txt
    priority_counts = {"see_now": 0, "today": 0, "routine": 0}
    category_counts = {cat: 0 for cat in sorted(ALLOWED_CATEGORIES)}
    hourly_counts = {}
    
    for r in sorted_records:
        # Priority counts
        p = r["priority"]
        priority_counts[p] = priority_counts.get(p, 0) + 1
        
        # Category counts
        c = r["category"]
        category_counts[c] = category_counts.get(c, 0) + 1
        
        # Hourly counts (e.g., '09:05' -> '09:00 - 09:59')
        hour_prefix = r["time"].split(":")[0]
        hour_label = f"{hour_prefix}:00 - {hour_prefix}:59"
        hourly_counts[hour_label] = hourly_counts.get(hour_label, 0) + 1

    # 4. Write summary.txt (Privacy-preserving administrative report)
    with open(summary_output_path, mode="w", encoding="utf-8") as f:
        f.write("=====================================================\n")
        f.write("      HEALTH CENTRE DAILY TRIAGE SUMMARY REPORT      \n")
        f.write("=====================================================\n\n")
        f.write(f"Total Student Visits Processed: {len(sorted_records)}\n\n")
        
        f.write("--- BREAKDOWN BY PRIORITY LEVEL ---\n")
        f.write(f"  - see_now : {priority_counts.get('see_now', 0)} (Immediate attention required)\n")
        f.write(f"  - today   : {priority_counts.get('today', 0)} (Same-day consultation)\n")
        f.write(f"  - routine : {priority_counts.get('routine', 0)} (Certificates / non-urgent)\n\n")
        
        f.write("--- BREAKDOWN BY SYMPTOM CATEGORY ---\n")
        for cat, count in category_counts.items():
            f.write(f"  - {cat:<10}: {count}\n")
        f.write("\n")
        
        f.write("--- BREAKDOWN BY ARRIVAL HOUR ---\n")
        for hour in sorted(hourly_counts.keys()):
            f.write(f"  - {hour}: {hourly_counts[hour]} visits\n")
        f.write("\n=====================================================\n")
        f.write("Note: This summary contains aggregate operational data only.\n")
        f.write("Patient personal notes are restricted to nurse_queue.csv.\n")
        f.write("=====================================================\n")
        
    print(f"[Output] Successfully generated: {summary_output_path}")
    return sorted_records


def main():
    print("=====================================================")
    print(" AI HEALTH CENTRE - CLINIC VISIT SORTER (FULL RUN)   ")
    print("=====================================================\n")
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY is missing! Check your .env file.")
    
    # Initialize Groq client
    client = Groq(api_key=api_key)
    
    # Load system prompt
    prompt_file = "system_prompt.txt"
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(f"Missing system prompt file: {prompt_file}")
    with open(prompt_file, "r", encoding="utf-8") as f:
        system_prompt = f.read()
    
    # 1. Load visits from CSV
    visits_file = "visits.csv"
    print(f"Loading student visits from '{visits_file}'...")
    visits = load_visits(visits_file)
    print(f"Loaded {len(visits)} student visits.\n")
    
    processed = []
    
    # 2. Process each note through the triage pipeline
    print("Beginning LLM classification and deterministic safety pipeline...")
    for idx, visit in enumerate(visits, start=1):
        v_id = visit["id"]
        v_time = visit["time"]
        v_note = visit["note"]
        
        print(f"[{idx:02d}/{len(visits)}] Processing {v_id} ({v_time}): \"{v_note[:45]}...\"")
        
        # Step A: LLM Classification with retry & fallback
        llm_output = classify(client, v_note, system_prompt)
        initial_priority = llm_output["priority"]
        category = llm_output["category"]
        raw_summary = llm_output["summary"]
        
        # Step B: Deterministic Red-Flag Check (Priority can only go UP)
        final_priority = raise_priority(v_note, initial_priority)
        if final_priority != initial_priority:
            print(f"       -> [ESCALATION] Red flag detected! Priority raised from '{initial_priority}' to '{final_priority}'")
            
        # Step C: Deterministic No-Diagnosis Scrubbing
        final_summary = remove_diagnosis(raw_summary)
        if final_summary != raw_summary:
            print(f"       -> [DIAGNOSIS SCRUBBED] Diagnostic terms replaced with neutral summary.")
            
        processed.append({
            "id": v_id,
            "time": v_time,
            "priority": final_priority,
            "category": category,
            "summary": final_summary,
            "original_note": v_note
        })
        
    print("\nAll visit notes processed successfully.")
    
    # 3. Write output files
    print("\nWriting output files...")
    sorted_records = write_reports(processed)
    
    # 4. Display the Final Prioritized Nurse Queue on the console
    print("\n" + "=" * 95)
    print("                      FINAL PRIORITIZED NURSE QUEUE (TRIAGE ORDER)")
    print("=" * 95)
    print(f"{'Q#':<4} | {'ID':<4} | {'TIME':<5} | {'PRIORITY':<9} | {'CATEGORY':<10} | {'SYMPTOM SUMMARY':<45}")
    print("-" * 95)
    
    current_tier = None
    for q_num, r in enumerate(sorted_records, start=1):
        # Print a separator between priority groups
        if current_tier != r["priority"]:
            current_tier = r["priority"]
            if q_num > 1:
                print("-" * 95)
                
        prio_tag = f"[{r['priority'].upper()}]"
        print(f"{q_num:<4} | {r['id']:<4} | {r['time']:<5} | {prio_tag:<9} | {r['category']:<10} | {r['summary'][:45]:<45}")
        
    print("=" * 95)
    print(f"Total Students in Queue: {len(sorted_records)} (All students will be seen by the nurse)")
    print("Output saved to 'nurse_queue.csv' and 'summary.txt'.")
    print("=" * 95 + "\n")


if __name__ == "__main__":
    main()
