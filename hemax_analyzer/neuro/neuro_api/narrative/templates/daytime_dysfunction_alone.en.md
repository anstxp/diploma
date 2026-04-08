# Daytime dysfunction — fatigue, sleepiness, reduced function
icon: 😪
severity: medium
---
The model detected elevated risk of daytime sleepiness and fatigue ({{ p_daytime_dysfunction }}%, ×{{ ratio_daytime_dysfunction }}). Your nighttime sleep **isn't restoring** as it should.

{% if sleep_hours_avg and sleep_hours_avg >= 7 and sleep_hours_avg <= 9 %}Interesting: you reported a normal sleep duration ({{ sleep_hours_avg }}h), yet the fatigue is there. This means **the problem is sleep quality, not quantity** — typical for apnea, circadian disruption, depression, or medical causes (hypothyroidism, anemia, B12 deficiency).
{% elif sleep_hours_avg and sleep_hours_avg < 6.5 %}Logical: you sleep {{ sleep_hours_avg }}h — below norm, so fatigue follows. First step is more sleep.
{% endif %}
{% if snoring and witnessed_apnea %}**Snoring + witnessed breathing pauses** = **classic obstructive sleep apnea**. Most common cause of adult daytime fatigue, especially with BMI >27. Urgent sleep-specialist referral + polysomnography.
{% elif snoring %}You snore — combined with daytime fatigue, this **strongly suggests sleep apnea**, especially with extra weight or large neck circumference.
{% endif %}
{% if has_hypothyroidism or on_thyroid_meds %}Your profile shows hypothyroidism — **verify your levothyroxine dose is adequate** (TSH check).
{% endif %}
{% if has_diabetes %}In diabetes, daytime fatigue can signal inadequate glycemic control (HbA1c >7) or nocturnal hypoglycemia.
{% endif %}

Among the model's top drivers — **sex** (women report this more often) and **RDW** (chronic inflammation marker). {% if ferritin and ferritin < 30 %}Your ferritin {{ ferritin }} ng/mL is low — iron deficiency often presents as fatigue.{% endif %}
---
actions:
- Check **ferritin**, **vitamin D**, **TSH**, **B12** — the most common hidden causes of fatigue
{% if snoring %}- **Polysomnography or home sleep test** — gold standard for apnea diagnosis{% endif %}
{% if not exercise_minutes_per_week or exercise_minutes_per_week < 90 %}- Moderate aerobic activity {{ "(at least 90 min/week)" if not exercise_minutes_per_week else "(currently {} min/wk — work up to 150)".format(exercise_minutes_per_week) }} — paradoxically gives more energy{% endif %}
- Morning sunlight 10-15 min — regulates circadian rhythm better than coffee
- Consistent sleep schedule, 7-9 hours regularly
- Avoid long daytime naps (>30 min) — they fragment night sleep
{% if caffeine_servings_per_day and caffeine_servings_per_day >= 4 %}- You consume {{ caffeine_servings_per_day }} caffeine servings — paradoxically this **worsens daytime fatigue** via the "caffeine cycle". Taper gradually{% endif %}
{% if alcohol_regular %}- Regular alcohol — the main cause of "shattered" wakefulness{% endif %}
- If chronic fatigue >6 months despite these steps — full evaluation including depression screen
---
red_flags:
- Falling asleep at the wheel — **stop driving** until medical evaluation
{% if snoring %}- Snoring or breathing pauses per partner — **see a sleep specialist**{% endif %}
- Chronic fatigue >6 months with muscle pain — chronic fatigue / fibromyalgia?
- Unexplained weight loss, night sweats + fatigue — urgent evaluation
{% if has_diabetes %}- Sudden severe fatigue + thirst + frequent urination — possible diabetes decompensation{% endif %}
