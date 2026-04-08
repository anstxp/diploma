# {% if on_antidepressants %}Current depression treatment — effectiveness review{% elif phq9_score and phq9_score >= 10 %}Your PHQ-9 indicates moderate depression{% else %}Possible depression signal{% endif %}
icon: 💙
severity: medium
---
{% if on_antidepressants %}Your profile shows you're on antidepressants. The model gives a moderate+ depression probability of {{ p_depression_moderate }}% — this **doesn't mean treatment failure**: antidepressant effects on lab markers are indirect, and the model may pick up residual symptoms or physiological correlates (ferritin, vitamin D, RDW) associated with depression.

{% if phq9_score %}You reported PHQ-9 = **{{ phq9_score }}**{% if phq9_score < 5 %} — this is **remission** ({{ phq9_score }} < 5). Therapy is working — continue.{% elif phq9_score < 10 %} — this is **partial response** (mild residual symptoms). Discuss with your doctor whether to adjust dose.{% elif phq9_score < 15 %} — this is **moderate** depression despite treatment. Re-evaluation needed — possibly switch med, add psychotherapy, or screen for bipolar disorder.{% else %} — this is **significant worsening**. Urgent contact with psychiatrist or GP.{% endif %}{% else %}A PHQ-9 screen with your doctor would help quantify current symptom level.{% endif %}
{% else %}The model detected elevated risk of moderate+ depression ({{ p_depression_moderate }}%, ×{{ ratio_depression_moderate }}). This is not a diagnosis but **a signal for evaluation**.

{% if phq9_score %}You reported PHQ-9 = **{{ phq9_score }}** — {% if phq9_score < 5 %}**minimal** symptoms by questionnaire, which doesn't fully match the model's prediction. The model may be responding to lab markers (vitamin D, ferritin){% elif phq9_score < 10 %}**mild** depression{% elif phq9_score < 15 %}**moderate** depression — confirms model prediction{% elif phq9_score < 20 %}**moderately severe** depression{% else %}**severe** depression — urgent consultation needed{% endif %}.{% endif %}

{% if recent_life_stressors %}You reported major life stressors — common trigger for depressive episodes, especially with genetic predisposition or prior episodes.{% endif %}
{% if has_chronic_pain or chronic_pain %}Chronic pain and depression are **closely interconnected**: pain causes depression, depression amplifies pain perception. Treating one usually improves the other.{% endif %}
{% if social_support_low %}You reported low social support — isolation significantly worsens depression. Connection sometimes matters more than meds.{% endif %}
{% endif %}
---
actions:
{% if on_antidepressants %}- **Don't stop antidepressants abruptly** — risk of relapse or discontinuation syndrome. Any change with your doctor only
- Regular contact with your doctor (every 1-3 months)
- Psychotherapy (CBT, IPT) — synergistic with antidepressants
- Sleep, activity, nutrition — foundation of treatment
{% else %}- **See a GP or psychiatrist** for PHQ-9, GAD-7 and clinical evaluation
- Psychotherapy (CBT, IPT) — first-line for mild-to-moderate depression
- Regular physical activity (150 min/wk aerobic) — effectiveness comparable to antidepressants for mild depression{% endif %}
{% if exercise_minutes_per_week is none or exercise_minutes_per_week < 90 %}- Moderate aerobic activity {{ "(at least 90 min/week to start)" if exercise_minutes_per_week is none else "(now {} min — increase to 150)".format(exercise_minutes_per_week) }}{% endif %}
- Check **vitamin D**, **B12**, **TSH**, **folate** — deficiencies mimic or worsen depression
- Morning sunlight 10-15 min
- Limit alcohol — it's a depressant
{% if social_support_low %}- Specifically work on connections with people — therapist can help{% endif %}
{% if recent_life_stressors %}- Consider grief/adjustment-focused therapy{% endif %}
---
red_flags:
- **Thoughts of suicide or self-harm — see a doctor urgently or call a crisis line**
- Psychosis: hallucinations, delusions, disorganization — emergency psychiatric care
- Sudden "improvement" + giving away possessions + farewells — elevated suicide risk
- Manic symptoms (hyperactivity, can't sleep, grandiose ideas) — screen for bipolar disorder
{% if on_antidepressants %}- Sudden mood change, severe anxiety or agitation on antidepressants — notify your doctor{% endif %}
