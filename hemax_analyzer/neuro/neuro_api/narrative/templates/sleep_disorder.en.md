# {% if snoring and witnessed_apnea %}Suspected obstructive sleep apnea{% elif sleep_latency_min and sleep_latency_min > 30 and night_awakenings and night_awakenings >= 3 %}Insomnia — combined pattern{% else %}Sleep disorder — combined profile{% endif %}
icon: 😴
severity: high
---
The model detected **simultaneous sleep deficiency and daytime dysfunction** — a classic sleep-disorder pattern.

{% if snoring and witnessed_apnea %}🚨 **Key finding:** you snore and your partner has observed **breathing pauses during sleep**. This is **the classic picture of obstructive sleep apnea (OSA)** — it causes dozens of micro-awakenings per night you may not remember, but which completely destroy restorative sleep. **OSA substantially raises risk of hypertension, MI, stroke, motor-vehicle crashes**. This isn't "just snoring" — it's **a treatable medical condition**.
{% elif sleep_latency_min and sleep_latency_min > 30 and night_awakenings and night_awakenings >= 3 %}Your pattern looks like **chronic insomnia**:
- Sleep latency {{ sleep_latency_min }} min (norm ≤20)
- Awakenings/night: {{ night_awakenings }} (norm 0-2)
This meets **DSM-5 criteria** for insomnia if it persists ≥3 nights/week >3 months.
{% else %}Could be insomnia, OSA, fragmented sleep, or a circadian disorder — each needs a specific approach.
{% endif %}

Chronically poor sleep doesn't just reduce quality of life — it **directly raises risk** of hypertension, type-2 diabetes, depression, cognitive impairment, accidents.

{% if shift_work %}Your shift schedule **significantly complicates** things — the human circadian rhythm doesn't fully adapt to shifts, even after years of working them.{% endif %}
{% if recent_life_stressors %}You reported major life stressors — acute stress often triggers insomnia, which then becomes chronic via "learned response".{% endif %}
---
actions:
- **See a GP or sleep specialist**{% if snoring and witnessed_apnea %} — **within 2 weeks, don't delay**{% endif %}
{% if snoring %}- **Polysomnography** (overnight study) — gold standard. Alternative: home sleep test{% endif %}
- Check **ferritin**, **vitamin D**, **TSH**, **B12** — deficiencies common in sleep disorders
- Consistent schedule (same bed/wake times ±30 min including weekends)
- 7-9 hours per night for adults
- Dark, cool (18-20°C) bedroom; no screens 1 hour before bed
- Caffeine — none after 2 PM; limit alcohol (it fragments sleep)
{% if not snoring %}- If bedtime anxiety is involved — **CBT-I** has better evidence than sleeping pills (try Sleepio or similar){% endif %}
{% if on_sleep_meds or uses_sleep_meds %}- Current sleep meds: discuss review — **benzodiazepines** aren't first-line, especially in older adults (fall, delirium risk){% endif %}
{% if shift_work %}- Bright-light therapy 10,000 lux in the morning after a night shift{% endif %}
---
red_flags:
- **Falling asleep at the wheel — stop driving immediately and seek care**
{% if snoring %}- **Witnessed breathing pauses — this is apnea, urgent sleep-specialist referral**{% endif %}
- Chronic insomnia (≥3 nights/week >3 months)
- Daytime sleepiness despite 7-9 hours — narcolepsy/apnea
- Depression symptoms + insomnia — they reinforce each other, need integrated treatment
{% if shift_work %}- Chronic shift work + obesity + snoring = doubled MI risk{% endif %}
