# Atherogenic dyslipidemia
icon: 💗
severity: medium
---
You have the combination of **low HDL ({{ hdl }} mg/dL) + high triglycerides ({{ trigly }} mg/dL)**. This is the classic picture of **atherogenic dyslipidemia** — a lipid pattern that strongly raises cardiovascular risk.

{% if on_statins %}
You're on statins, but the lipid profile is still atherogenic — this means **current therapy isn't enough**. Don't worry: statins work well on LDL but don't do much for HDL or triglycerides. The treatment plan needs review with your cardiologist.
{% elif has_diabetes %}
You have diabetes, which already raises cardiovascular risk. Combined with this dyslipidemia, the risk of MI/stroke is substantially higher — tighter control is needed. Target LDL for diabetics: <70 mg/dL (not <100 as in the general population).
{% elif has_cardiovascular_disease %}
Since you've had a cardiovascular event (MI, stroke, or established CAD), this lipid pattern **substantially raises the risk of recurrence**. Aggressive secondary prevention is needed.
{% else %}
Often accompanies insulin resistance, metabolic syndrome, abdominal obesity. Good news — even small lifestyle changes give significant improvements.
{% endif %}
---
actions:
{% if on_statins %}
- **See a cardiologist** — discuss intensifying therapy (higher statin dose, adding ezetimibe, fibrates, or omega-3)
- Check adherence: are you taking statins regularly, at the right time, with food
- Test ALT and creatine kinase — make sure current dose isn't causing side effects
- Review diet and exercise — even on statins they're critical
{% elif has_diabetes %}
- **See an endocrinologist or cardiologist** — discuss starting statins (recommended for all diabetics ≥40)
- Target LDL for diabetics: **<70 mg/dL**, not <100 as in the general population
- Review glycemic control — hyperglycemia worsens dyslipidemia
- Diet: minimize refined carbs, alcohol, trans fats
{% elif has_cardiovascular_disease %}
- **Urgently see a cardiologist** for secondary prevention review
- If not on statins yet — they should be started (target LDL <55 after the event)
- May need additional drugs: antiplatelets, beta blockers, ACE inhibitors
{% else %}
- See a GP or cardiologist for full CV risk evaluation
- Get tested: HbA1c, repeat fasting lipids, ALT (liver assessment)
- Lifestyle: Mediterranean diet, limit refined carbs and alcohol
- 150 min/week aerobic + 2 strength sessions
- If overweight: aim for 5-10% weight loss
- If other risk factors present, discuss statins with your doctor
{% endif %}
---
red_flags:
- Chest pain, dyspnea on exertion
- Family history of early heart attacks
{% if not has_diabetes %}
- New diabetes symptoms (thirst, frequent urination, weight loss)
{% endif %}
{% if on_statins %}
- Severe muscle pain or dark urine — possible statin-induced rhabdomyolysis
{% endif %}
