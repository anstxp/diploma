# Critically low sodium
icon: 🔴
severity: high
---
Your sodium ({{ sodium }} mmol/L) is **critically low**. At ≤125 mmol/L, seizures, cerebral edema, and coma are possible. This is **an emergency**.

{% if on_diuretics %}
**Most likely cause — diuretics**, especially thiazides (hydrochlorothiazide, indapamide). Thiazides are the **#1 cause of medication-induced hyponatremia**, particularly in elderly women. The drug isn't "bad" — but this dose/type doesn't suit you.
{% elif has_cardiovascular_disease %}
You have cardiovascular disease — heart failure often causes hyponatremia through ADH activation. Decompensation is a frequent cause.
{% elif has_liver_disease %}
You have liver disease — cirrhosis with ascites often causes hyponatremia through fluid redistribution and water retention. It's a marker of decompensation.
{% else %}
Causes: SIADH (inappropriate ADH secretion), severe heart or liver failure, excessive water intake, diuretics, hypothyroidism, adrenal insufficiency.
{% endif %}
---
actions:
- **Go to the ER today**
- Don't drink large amounts of water before evaluation
- Bring a list of medications, especially diuretics
- Possible hospital admission for controlled correction
- **Rapid correction can be dangerous** — needs careful monitoring
{% if on_diuretics %}
- **Don't stop the diuretic on your own** — the ER will decide whether to discontinue, switch, or reduce dose
- Tell the doctor the exact drug name and dose — critical for management
{% endif %}
---
red_flags:
- Severe headache, nausea, vomiting
- Confusion, disorientation
- Muscle cramps or twitching
- Drowsiness, decreased responsiveness
- Loss of consciousness, seizures — **call EMS**
