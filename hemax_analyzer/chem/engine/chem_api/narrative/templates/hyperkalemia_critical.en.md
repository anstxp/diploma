# Critically high potassium — danger to the heart
icon: 🔴
severity: high
---
Your potassium ({{ potassium }} mmol/L) is **critically high**. At ≥6.0 mmol/L there's a real **risk of dangerous heart arrhythmias**, up to cardiac arrest. This is **an emergency**.

{% if on_acei_arb and has_ckd %}
**Most likely the cause is the combination**: you're on an ACE inhibitor / ARB with CKD. These drugs raise potassium, and the kidneys can't clear it efficiently. **Don't wait — go to the ER!**
{% elif on_acei_arb %}
You're on an ACE inhibitor / ARB — these drugs **commonly cause hyperkalemia**, especially combined with other factors. The ER team must know this.
{% elif has_ckd %}
You have CKD — kidneys can't efficiently clear excess potassium, so any trigger (diet, medication) leads to critical elevation.
{% elif on_diuretics %}
You're on diuretics — if K-sparing (spironolactone, eplerenone), they may be the cause. The ER will sort this out.
{% else %}
Most common causes: severe CKD, certain medications (ACE-I, ARBs, spironolactone, NSAIDs), massive cell breakdown (trauma, burns), diabetic ketoacidosis.
{% endif %}
---
actions:
- **Go to the ER immediately** — don't wait until tomorrow
- Don't take: potassium supplements, salt substitutes (KCl), bananas/apricots/potatoes until evaluated
- Bring a list of all medications
- Likely needs ECG and emergency potassium-lowering measures
{% if on_acei_arb %}
- **Don't stop the ACE-I / ARB on your own** — the ER will decide whether to discontinue, reduce, or switch
{% endif %}
{% if on_diuretics %}
- Tell the doctor exactly which diuretic — critical for management
{% endif %}
---
red_flags:
- Palpitations, "skipped" heartbeats
- Muscle weakness, especially in legs
- Tingling or numbness
- Irregular pulse
- Shortness of breath
