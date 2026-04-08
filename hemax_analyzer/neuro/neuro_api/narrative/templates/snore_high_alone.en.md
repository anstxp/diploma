# {% if snoring and witnessed_apnea %}Possible sleep apnea — testing recommended{% elif snoring %}Snoring + signs of disordered breathing in sleep{% else %}Elevated risk of sleep-disordered breathing{% endif %}
icon: 😴
severity: {% if snoring and witnessed_apnea %}high{% elif snoring %}medium{% else %}medium{% endif %}
---
The model estimates your risk of sleep-disordered breathing (snore high) at **{{ p_snore_high }}%** ({% if ratio_snore_high %}×{{ ratio_snore_high }} vs. baseline{% else %}elevated risk{% endif %}). This combines objective factors (age, weight, neck circumference, blood pressure) with your self-reported sleep data.
{% if snoring %}You reported that **you snore**.{% endif %}
{% if witnessed_apnea %} **Your partner has witnessed pauses in your breathing during sleep** — this is a classic symptom of obstructive sleep apnea (OSA).{% endif %}
{% if witnessed_apnea %}

OSA is not just "loud snoring". It's repeated episodes of breathing cessation that drop blood oxygen, fragment sleep, and raise the risk of hypertension, heart attack, stroke, and daytime micro-sleep crashes.{% elif snoring %}

Not every snore is apnea. But snoring combined with morning fatigue, headaches, elevated morning blood pressure, or daytime sleepiness is worth testing.{% endif %}
---
actions:
{% if snoring and witnessed_apnea %}- **See a sleep specialist** for polysomnography (overnight sleep study) — the gold standard for OSA diagnosis
- Avoid driving if you have noticeable daytime sleepiness — high risk of micro-sleep at the wheel{% else %}- If snoring goes with morning fatigue, headaches, or elevated morning blood pressure — **discuss a polysomnography referral with your doctor**
- Try avoiding **sleeping on your back** (snoring is often worse in supine position) — switch to side sleeping{% endif %}
{% if alcohol_regular %}- **Evening alcohol** relaxes throat muscles and worsens apnea — try 2 weeks without evening alcohol and compare{% endif %}
- Manage weight: even **5-10% weight reduction** significantly improves OSA
- If you have hypertension + snoring — that's a common pairing; blood pressure control reduces complication risk
- Sleep hygiene: cool bedroom, regular schedule, no heavy meals within 3h of bed
---
red_flags:
{% if witnessed_apnea %}- **Witnessed apnea is a signal to schedule polysomnography promptly** — don't delay{% endif %}
- Severe **daytime sleepiness**, micro-sleep at work or while watching TV — dangerous when driving
- Morning headaches + dry mouth + unrefreshing sleep — classic OSA triad
- Hypertension that's hard to control, especially combined with snoring — get screened for apnea
