# {% if sleep_latency_min and sleep_latency_min > 30 %}Trouble falling asleep + impaired sleep quality{% else %}Elevated risk of chronic sleep problems{% endif %}
icon: 🛏️
severity: medium
---
The model estimates your risk of chronic sleep problems (trouble sleeping high) at **{{ p_trouble_sleeping_high }}%** ({% if ratio_trouble_sleeping_high %}×{{ ratio_trouble_sleeping_high }} vs. baseline{% else %}elevated risk{% endif %}). Unlike sleep deficiency (too few hours), this is about sleep **quality** — whether you fall asleep easily, stay asleep, and wake up feeling rested.

{% if sleep_latency_min %}Your sleep-onset time: **{{ sleep_latency_min }} min**. {% if sleep_latency_min > 30 %}Normal is up to 20 min. Taking >30 min to fall asleep meets the **clinical definition of insomnia** if it happens ≥3 nights/week for over 3 months.{% endif %}{% endif %}
{% if night_awakenings and night_awakenings >= 3 %}You wake **{{ night_awakenings }} times per night** — this fragments sleep cycles and reduces the restorative function of sleep.{% endif %}
{% if early_morning_awakening %} Early-morning awakening without being able to fall back asleep is a **classic feature of depressive episodes**, especially when paired with low morning mood.{% endif %}

{% if on_anxiolytics or on_sleep_meds %}You already take medications that affect sleep. These don't **treat** chronic insomnia — they mask symptoms, so the long-term strategy is different.{% else %}Chronic insomnia is not "stress-related sleep loss". It's a distinct medical condition with a more effective treatment than sleeping pills: **CBT-I** (cognitive behavioural therapy for insomnia), typically a 6-8 session structured programme.{% endif %}
---
actions:
- **Consistent schedule** — go to bed and wake up at the same time **even on weekends** (±30 min). This is the single strongest sleep-regulating factor
{% if sleep_latency_min and sleep_latency_min > 30 %}- **The 20-minute rule**: if you can't fall asleep in 20 min, get up, do something quiet in dim light, return to bed only when sleepy. Bed = sleep only.
- Don't try to "force" sleep — that's the fastest path to anxious sleep anticipation, which then becomes its own problem{% endif %}
{% if caffeine_servings_per_day and caffeine_servings_per_day >= 2 %}- You consume {{ caffeine_servings_per_day }} caffeine servings/day — half-life is 5-6 hours, so **no caffeine after 2 PM**{% endif %}
{% if screen_time_before_bed_min and screen_time_before_bed_min >= 30 %}- {{ screen_time_before_bed_min }} min of screen time before bed — blue light suppresses melatonin, try cutting back 60 min before sleep{% endif %}
{% if alcohol_regular %}- Regular alcohol — it helps you fall asleep but **wrecks the second half of the night** (REM and deep sleep). Try 2 weeks alcohol-free and compare your subjective morning freshness{% endif %}
- **CBT-I** (cognitive behavioural therapy for insomnia) — more effective than sleeping pills long-term, very strong evidence base. Look for a certified provider or a CBT-I app (Sleepio, Stellar Sleep)
- Cool bedroom (18-20°C), quiet, dark — basic, but it works
---
red_flags:
- Severe **daytime sleepiness**, micro-sleeps during the day, can't concentrate — affects safety (driving, machinery)
- **Early-morning awakening + low mood + loss of interest** — screen for depression, not insomnia
- Dependence on sleeping pills, especially benzodiazepines — **taper only under medical supervision**, abrupt cessation can cause rebound insomnia and anxiety
- Sleep problems ≥3 nights/week for over 3 months = **chronic insomnia** — treat as its own condition, not a symptom
