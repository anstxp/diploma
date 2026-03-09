# Elevated uric acid
icon: 🦴
severity: low
---
Your uric acid ({{ uric_acid }} mg/dL) is above normal. This is **hyperuricemia** — a risk factor for **gout** and kidney stones.

{% if on_diuretics %}
**Thiazide diuretics (hydrochlorothiazide, indapamide) are one of the most common causes** of hyperuricemia in adults — they raise uric acid in about 50% of patients. This doesn't mean they should be stopped — for many, the BP benefit outweighs this risk. But if you've had gout attacks, discuss alternatives with your doctor.
{% elif has_ckd %}
You have CKD — kidneys excrete uric acid, so levels naturally rise as kidney function declines. Self-treatment **won't help** — you need CKD management.
{% elif has_cardiovascular_disease %}
You have cardiovascular disease — hyperuricemia adds to CV risk and often accompanies metabolic syndrome.
{% else %}
Not everyone with high uric acid develops gout — it depends on genetics, lifestyle, diuretics. But **elevated uric acid alone** is associated with higher CV risk.
{% endif %}
---
actions:
{% if on_diuretics %}
- **If you've had gout attacks** — discuss alternatives (e.g., losartan, an ARB that lowers uric acid)
- Don't stop the diuretic on your own
- Test creatinine, recheck uric acid in a month
- Diet: reduce red meat, seafood, beer
- Drink enough water (2-3 L/day)
{% elif has_ckd %}
- Show results to a nephrologist
- If uric acid >10 mg/dL or you've had gout — allopurinol may be needed
- CKD management is the foundation
{% else %}
- See your GP for context evaluation
- Get tested: creatinine (kidneys excrete uric acid), HbA1c, lipid panel
- Diet: limit red meat, seafood, organ meats, beer, fructose-sweetened drinks
- Drink enough water (2-3 L/day)
- If overweight, weight loss helps
- If on diuretics, discuss with your doctor
{% endif %}
---
red_flags:
- **Acute joint pain and swelling** (especially big toe) — possible gout attack
- Flank pain, blood in urine — possible kidney stones
{% if has_cardiovascular_disease %}
- Acute chest pain — hyperuricemia adds to CV risk
{% endif %}
