# {% if sleep_hours_avg and sleep_hours_avg < 5 %}Chronic short sleep — needs attention{% elif sleep_hours_avg and sleep_hours_avg < 6.5 %}Sleep is below what you need{% else %}Sleep deficiency{% endif %}
icon: 🌙
severity: {% if sleep_hours_avg and sleep_hours_avg < 5 %}high{% else %}medium{% endif %}
---
{% if sleep_hours_avg %}You reported sleeping **{{ sleep_hours_avg }} h/night** on average.{% if sleep_hours_avg < 5 %} This is a **serious deficit** — chronic sleep <5h is linked with higher risk of hypertension, diabetes, depression, and motor-vehicle crashes from microsleeps.{% elif sleep_hours_avg < 6.5 %} That's **below the recommended 7-9 h** for adults. Chronically short sleep gradually accumulates "sleep debt".{% elif sleep_hours_avg > 9 %} That's **longer than the norm** — excess sleep in adults can be a marker of depression, sleep apnea, or hypothyroidism.{% endif %}
{% else %}Your profile suggests elevated risk of sleep deficiency ({{ p_sleep_deficiency }}%, ×{{ ratio_sleep_deficiency }}). This may mean short sleep or difficulty falling asleep.{% endif %}

{% if sleep_latency_min and sleep_latency_min > 30 %}It takes you **{{ sleep_latency_min }} min** to fall asleep — that's long. Common causes: bedtime anxiety, irregular schedule, late caffeine.{% endif %}
{% if night_awakenings and night_awakenings >= 3 %}You wake up **{{ night_awakenings }} times per night** — this fragments sleep cycles and reduces restorative function.{% endif %}
{% if early_morning_awakening %}Waking up much earlier than intended without being able to return to sleep is **a characteristic feature of a depressive episode**, especially together with low morning mood.{% endif %}
{% if shift_work %}You work shift hours — this is **a standalone cause** of circadian disruption regardless of other factors.{% endif %}

{% if on_sleep_meds or uses_sleep_meds %}**Note:** you already use sleep aids. Chronic use (especially benzodiazepines and Z-drugs) can paradoxically worsen sleep quality and create dependence. This is a **topic for your doctor**, not for self-adjustment.{% endif %}
{% if not on_sleep_meds and not uses_sleep_meds %}Interesting: the model identifies **vitamin D** as a top driver of this prediction{% if vit_d %} (your level: {{ vit_d }} ng/mL){% endif %} — this nutrient is linked to circadian rhythm regulation.{% endif %}
---
actions:
- Target **7-9 hours per night**{% if sleep_hours_avg and sleep_hours_avg < 6 %} — gradually, +30 min/week, not abruptly{% endif %}
{% if sleep_latency_min and sleep_latency_min > 30 %}- Sleep hygiene: bed for sleep only, cool room (18-20°C), no screens 1 hour before bed
- If not asleep in 20 min — get up, do something calm under dim light, return to bed when sleepy{% endif %}
{% if night_awakenings and night_awakenings >= 3 %}- Frequent awakenings + snoring → **sleep study (polysomnography)** to rule out apnea{% endif %}
{% if caffeine_servings_per_day and caffeine_servings_per_day >= 3 %}- You consume {{ caffeine_servings_per_day }} caffeine servings/day — limit to 2, **none after 2 PM**{% endif %}
{% if screen_time_before_bed_min and screen_time_before_bed_min >= 30 %}- {{ screen_time_before_bed_min }} min screen time before bed — try blue-light filters or stop 60 min earlier{% endif %}
{% if shift_work %}- **Shift work** + <7h sleep doubles metabolic risk. Morning light therapy after a night shift helps{% endif %}
{% if alcohol_regular %}- Regular alcohol — it helps you fall asleep but **wrecks the second half of the night** (REM and deep sleep). Try 2 weeks without and compare{% endif %}
- Consistent schedule: same bed/wake times, **including weekends** (±30 min)
- Persistent insomnia ≥3 nights/week >3 months → **CBT-I has better evidence than sleeping pills**
---
red_flags:
- Severe **daytime sleepiness** affecting work or driving
{% if snoring and witnessed_apnea %}- **Snoring + witnessed breathing pauses — classic picture of obstructive sleep apnea, see a sleep specialist urgently**{% elif snoring %}- Snoring + morning headaches or severe daytime fatigue — possible apnea{% endif %}
{% if early_morning_awakening %}- Early-morning awakening + low mood + loss of interest — screen for depression{% endif %}
- Sleep-aid dependence — taper **only under medical supervision**
- Falling asleep at the wheel — **stop driving and seek medical evaluation**
