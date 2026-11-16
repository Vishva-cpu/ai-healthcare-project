# Cost and Latency Analysis: AI Clinic Visit Sorter

**System:** AI Health Centre Project – Clinic Visit Sorter  
**Provider & Model:** Groq API (`qwen/qwen3.8-27b`)  
**Deployment Context:** College Campus Health Centre (8-hour operational day)

---

## 1. Operational Volume Assumptions
* **Campus Population:** ~3,000 enrolled students.
* **Average Daily Health Centre Visits:** 80 to 120 visits per operating day.
* **Standard Planning Baseline:** **100 visits/day**.
* **Peak Surge Volume (e.g., flu season, sports events):** Up to 200 visits/day.

---

## 2. Token Utilization Breakdown per API Call

Each student visit triggers one primary LLM classification request (plus a retry only if an error occurs).

| Token Type | Component | Average Tokens per Call |
| :--- | :--- | :--- |
| **Input Tokens** | System Prompt (`system_prompt.txt` - 5 Roles + Exemplars) | ~420 tokens |
| **Input Tokens** | User Visit Note (Informal note string) | ~25 tokens |
| **Input Subtotal** | **Total Input Tokens per Note** | **~445 tokens** |
| **Output Tokens** | Structured JSON Response (`{"category": ..., "priority": ..., "summary": ...}`) | **~35 tokens** |
| **Total per Call** | **Combined Tokens per Transaction** | **~480 tokens** |

---

## 3. Empirical Latency Measurements

Empirical measurements gathered from our benchmark test runs:

* **Average Request Latency:** **304.5 ms (~0.30 seconds)**
* **Fastest Response:** **230.8 ms**
* **Slowest Response:** **601.0 ms**
* **Total Batch Processing Time (100 daily visits):**
  $$\text{Total Time} = 100 \times 0.305\text{ s} \approx 30.5\text{ seconds}$$
* **Clinical Impact:** A latency of 0.30 seconds is effectively instantaneous in a real-world clinic reception environment, meaning the nurse queue updates immediately upon note submission.

---

## 4. Cost Projection (Daily, Monthly, Annual)

### Scenario A: Groq Developer Free Tier
* Groq provides a generous free access tier (up to 30 requests per minute and 14,400 requests/day).
* **Daily Cost:** **\$0.00**
* **Monthly Cost:** **\$0.00**

### Scenario B: Commercial Pay-As-You-Go API Rates
Assuming standard cloud inference pricing:
* Input Token Rate: \$0.10 per 1,000,000 tokens
* Output Token Rate: \$0.30 per 1,000,000 tokens

$$\text{Daily Input Cost} = 100 \times 445 \times \frac{\$0.10}{10^6} = \$0.00445$$
$$\text{Daily Output Cost} = 100 \times 35 \times \frac{\$0.30}{10^6} = \$0.00105$$
$$\text{Total Daily Cost} \approx \$0.0055\text{ (less than 1 cent per day)}$$

| Horizon | Total Visits | Estimated Cost (USD) | Estimated Cost (INR) |
| :--- | :--- | :--- | :--- |
| **Per Day** | 100 visits | \$0.0055 | ~₹0.46 |
| **Per Month (22 operating days)** | 2,200 visits | \$0.1210 | ~₹10.16 |
| **Academic Year (200 days)** | 20,000 visits | \$1.1000 | ~₹92.40 |

---

## 5. Engineering Optimization Insights
1. **Prompt Caching / Low Token Bloat:** The system prompt is kept concise (~420 tokens) while retaining the full 5-role framework.
2. **Deterministic Pre-Filters:** High-volume non-medical forms could optionally be routed without LLM calls if needed, though at $0.005/day, LLM triage for all notes is extraordinarily cost-effective.
3. **Retry Budget:** By limiting retries strictly to 1 attempt, worst-case token consumption is bounded at $2\times$ baseline.

