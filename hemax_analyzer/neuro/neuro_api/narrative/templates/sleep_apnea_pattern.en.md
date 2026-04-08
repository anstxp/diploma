# Suspected obstructive sleep apnea
icon: 🚨
severity: high
---
🚨 **This is the most important finding in your report.** You reported **snoring + partner-witnessed breathing pauses during sleep**. This is the classic picture of **obstructive sleep apnea (OSA)** — a condition where the upper airway partially or completely collapses during sleep, causing dozens to hundreds of micro-awakenings per night.

You may not remember these awakenings, but **your body experiences them**: each time blood oxygen drops, the sympathetic nervous system fires, blood pressure spikes, the heart strains.

**OSA significantly raises risk of:**
- Hypertension (especially treatment-resistant)
- Myocardial infarction and stroke
- Atrial fibrillation
- Type 2 diabetes
- Motor-vehicle crashes from microsleeps (2-5× baseline)
- Late-life dementia

{% if bmi and bmi > 30 %}Your BMI {{ bmi }} is an **additional risk factor** for OSA (excess weight narrows the airway).
{% endif %}
{% if has_diabetes or has_hypertension %}If you have diabetes/hypertension already, OSA is often **the reason** for poor control — treating OSA significantly improves these conditions too.
{% endif %}
{% if sleep_hours_avg %}You sleep {{ sleep_hours_avg }}h — but **that's not "enough" if it's fragmented**. OSA patients often sleep 8 hours and wake exhausted.
{% endif %}

**The good news:** OSA is highly treatable. CPAP therapy (a nightly mask with continuous positive pressure) **completely eliminates symptoms** in most patients from the first night.
---
actions:
- **See a sleep specialist or pulmonologist within 2-4 weeks** — not an emergency, but don't delay for months
- **Polysomnography** (overnight lab study) or **home sleep test** — needed to confirm diagnosis and severity
- Complete the **STOP-BANG questionnaire** — helps your clinician estimate pretest probability
{% if bmi and bmi > 27 %}- **Weight loss** — even -5 kg can substantially improve OSA{% endif %}
- Sleep on your side (not your back) — simple but effective
- Avoid alcohol within 4 hours of bedtime (it relaxes throat muscles)
- Don't use sleep aids without medical guidance — some (benzodiazepines) **worsen** OSA
- Monitor blood pressure regularly — OSA often causes morning hypertension
---
red_flags:
- **Falling asleep at the wheel — stop driving until diagnosis and treatment**
- Chest pain or shortness of breath during nighttime awakenings
- Severe morning headaches — common in severe OSA
- Depression, irritability, loss of libido — also typical for long-untreated OSA
- Severe sleepiness despite adequate time in bed
