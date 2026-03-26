# {% if on_statins %}Statin therapy is working but needs monitoring{% elif has_high_chol %}Lipid control is stable, with room for improvement{% else %}Moderate cholesterol risk{% endif %}
icon: 💗
severity: low
---
{% if on_statins %}
You're on statins, and the current lipid model shows moderate risk ({{ p_high_chol }}%). **This means therapy is working, but targets can still be tightened** — especially if you have other CV risk factors.

{% if has_diabetes %}You have diabetes — LDL targets are **stricter** (usually <70 mg/dL at high risk, <55 at very high risk). Current level may not be low enough.{% endif %}
{% elif has_high_chol %}
Hypercholesterolemia is in your profile. Current lipid panel is stable (model shows {{ p_high_chol }}%), but there's room for improvement — especially with other risk factors present.
{% else %}
Moderately elevated cholesterol risk ({{ p_high_chol }}%). At this stage, **diet and activity yield the biggest gains**.
{% endif %}
---
actions:
{% if on_statins %}
- **Take statins consistently** — do not skip doses
- Discuss with cardiologist whether therapy should be intensified (higher dose, ezetimibe) based on LDL target
- Check ALT and creatine kinase — confirm current dose isn't causing side effects
- Diet and activity matter even on statins
- Repeat lipid panel in 3-6 months
{% else %}
- Repeat fasting lipid panel in 3 months
- Increase soluble fiber (oats, legumes, apples)
- Swap saturated for unsaturated fats (fish, olive oil, nuts)
- 150 min/week activity
- Limit trans fats and fast food
{% if has_diabetes %}- Glycemic control improves the lipid profile{% endif %}
{% endif %}
---
red_flags:
- Chest pain
- Familial dyslipidemia history — early screening
{% if on_statins %}- Severe muscle pain or dark urine — **possible statin rhabdomyolysis** — urgent medical attention{% endif %}
