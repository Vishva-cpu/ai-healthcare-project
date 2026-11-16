# Personal Reflection: Responsible AI Engineering in Healthcare Triage

**Author:** First-Year MSc Decision and Computing Science Student  
**Project:** AI Health Centre Project – Clinic Visit Sorter  
**Course:** CIT AI-Native Engineering Programme · Assessment 5  

---

As a first-year postgraduate student in Decision and Computing Science, building the Clinic Visit Sorter fundamentally reshaped my understanding of AI engineering. In academic coursework, machine learning problems often reduce to optimizing symmetric metrics like accuracy or F1-score on sanitized datasets. However, implementing an applied triage tool for a college health centre exposed me to the realities of high-stakes, safety-critical AI systems where algorithmic errors carry real human consequences.

The first profound lesson was the concept of **asymmetric risk**. In clinical decision support, false positives and false negatives are not created equal. Misclassifying an administrative certificate request as urgent is merely a minor inconvenience to the nurse. Conversely, misclassifying a student suffering from acute myocardial distress or anaphylaxis as routine could lead to fatal delay. This insight dictated my entire system architecture: **priority can only go up, never down**. I learned that responsible AI engineering requires embedding ethical safeguards directly into the decision logic rather than relying solely on the probabilistic output of an LLM.

The second key insight was the necessity of **defense-in-depth through hybrid architecture**. An LLM, no matter how advanced, is fundamentally probabilistic and subject to hallucination, schema drift, or adversarial manipulation. Relying on an API alone would be irresponsible. By pairing the Groq LLM with deterministic Python guardrails—specifically bilingual red-flag scanners, strict JSON schema validators, automated single retries, and regex-based diagnosis scrubbers—I created a resilient fail-safe boundary. Even when a student actively attempted prompt injection by begging for a `routine` label while experiencing chest tightness, or when a student baited the model for a prescription, the hybrid architecture defended the clinical boundary flawlessly.

Finally, navigating linguistic reality was an invaluable learning experience. College students in Tamil Nadu communicate their suffering through informal English, Tamil script, and transliterated Tanglish phrases like *“nenju vali”*, *“romba mudiyala”*, or *“moochu vida mudiyala”*. Building a localized red-flag dictionary taught me that inclusive AI must respect cultural and linguistic nuances rather than demanding formal, textbook clinical descriptions.

Ultimately, this project reinforced that the goal of AI in medicine is not to replace human experts, but to augment them responsibly. The triage nurse remains the indispensable human checkpoint, seeing every student and retaining full clinical autonomy. This experience has established my foundational philosophy as an aspiring AI engineer: build transparent, bounded, and human-centred systems that prioritize safety above all else.

