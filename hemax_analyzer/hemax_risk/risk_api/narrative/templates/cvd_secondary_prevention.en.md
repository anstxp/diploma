# Cardiovascular secondary prevention
icon: ❤️‍🩹
severity: medium
---
Your profile shows established cardiovascular disease (prior MI, CHD{% if had_stroke %}, prior stroke{% endif %}{% if has_chf %}, heart failure{% endif %}). This means you are in **secondary prevention** — the goal isn't to "lower risk from baseline" but to **prevent a recurrent event**.

**Important to understand:** the low risk numbers from the model ({{ p_chd | default('—') }}% for CHD) reflect **the fact that therapy is working**, not that risk has disappeared. Patients with known CVD have a **15-20%** 10-year risk of a recurrent event without therapy; your current regimen typically reduces this 2-3 fold.

{% if on_statins %}**Statin:** stabilises atherosclerotic plaques. LDL target for your group is **<55 mg/dL** (≤1.4 mmol/L).{% if ldl and ldl > 55 %} Your current LDL ({{ ldl }} mg/dL) is slightly above target — discuss dose intensification or adding ezetimibe with your cardiologist.{% endif %}{% endif %}
{% if on_acei_arb %}
**ACE inhibitor / ARB:** reduces post-MI cardiac remodelling and protects the kidneys.{% endif %}
{% if on_oral_anticoagulants %}
**Antiplatelet (aspirin) or anticoagulant:** prevents thrombosis in already-damaged vessels.{% endif %}
{% if has_diabetes %}
**Diabetes + CVD is an especially high-risk combination.** Typical HbA1c target ≤7%; LDL ≤1.4 mmol/L ("very high risk").{% endif %}
---
actions:
- **Do not stop current therapy on your own** — every dose matters
- Regular cardiology visits — every 6 months or more often per your physician
- Home BP monitoring (target <130/80)
- Lipid panel every 6-12 months
{% if on_statins %}- Check ALT and CK — monitor for statin side effects{% endif %}
- Mediterranean-style diet, limit salt and saturated fat
- Aerobic activity 150 min/week (coordinate intensity with cardiologist)
{% if has_diabetes %}- Annual: ophthalmology exam, foot check, urine microalbumin{% endif %}
- Don't skip doses — use a weekly pill organiser or reminder app
---
red_flags:
- **Chest pain**, especially on exertion or at rest > 5 min — see a doctor urgently or call emergency services
- Severe shortness of breath, nocturnal dyspnoea, leg swelling — signs of decompensation
- Sudden weakness in arm/leg, facial droop, speech difficulty — **suspect stroke, call emergency services**
- Palpitations, irregular heartbeat, dizziness — needs evaluation
{% if on_oral_anticoagulants %}- Blood in urine, black stools, large bruises — bleeding on anticoagulants{% endif %}
{% if on_statins %}- Severe muscle pain or dark urine — possible statin rhabdomyolysis{% endif %}
