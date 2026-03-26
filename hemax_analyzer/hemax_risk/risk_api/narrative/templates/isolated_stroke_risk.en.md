# {% if had_stroke %}Secondary stroke prevention{% elif has_cardiovascular_disease %}Elevated stroke risk on background of CVD{% else %}Elevated stroke risk{% endif %}
icon: 🧠
severity: high
---
{% if had_stroke %}
A prior stroke is in your profile, and current model shows **elevated risk of a recurrent event** ({{ p_stroke }}%). This means **secondary prevention needs review** — after the first stroke, the risk of a second is substantially higher.

{% if on_oral_anticoagulants %}You're on anticoagulants — continue consistently, **do not stop on your own**.{% endif %}
{% elif has_cardiovascular_disease %}
You have CVD in your profile, and the model shows **elevated stroke risk** ({{ p_stroke }}%, ×{{ ratio_stroke }}). CVD + this profile = heightened attention to BP, rhythm, and lipid control.
{% else %}
**Elevated stroke risk** ({{ p_stroke }}%, ×{{ ratio_stroke }}). Most strokes are preventable via BP, atrial-fibrillation, and lipid control.
{% endif %}
---
actions:
{% if had_stroke %}
- **Neurologist or cardiologist — unscheduled visit**
- ECG and Holter — detect atrial fibrillation if not yet diagnosed
- Carotid Doppler — repeat if not done recently
- Tight BP control — target <130/80
- LDL <55 mg/dL (secondary prevention after stroke)
- **Continue antiplatelet/anticoagulant therapy** consistently
{% elif has_cardiovascular_disease %}
- **Cardiologist or neurologist within 2-4 weeks**
- ECG and Holter — detect atrial fibrillation
- Carotid Doppler
- Tight BP control — target <130/80
- Lipid and glucose control
- If atrial fibrillation present — discuss anticoagulation
{% else %}
- **Cardiologist or neurologist within 2-4 weeks**
- ECG — detect atrial fibrillation
- Carotid Doppler — atherosclerosis
- Tight BP control — target <130/80
- If atrial fibrillation present — anticoagulants per physician
- Limit alcohol, quit smoking
- Glucose and lipid control
{% endif %}
---
red_flags:
- **F.A.S.T.** — Face droop, Arm weakness, Speech difficulty, Time to call — **call emergency**
- Sudden dizziness with balance problems
- Sudden severe headache, "worst of life"
- Sudden vision loss
