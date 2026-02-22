# Hemoglobin and red cells above normal
icon: 🔺
severity: medium
---
Your hemoglobin — {{ hgb }} g/dL — is **above the upper limit**. This is called erythrocytosis.

{% if smoker %}
**Smoking is the most likely cause.** Chronic smoking causes mild hypoxia (CO binds hemoglobin instead of oxygen), and the bone marrow responds by **producing more red cells**. This is a **compensatory reaction**, not a true disease — but it adds cardiovascular risk.

Quitting smoking is the most effective way to **lower erythrocytosis**. Counts usually normalize within 3-6 months of quitting.
{% elif has_cardiovascular_disease %}
You have cardiovascular disease — elevated red cells **increase thrombosis risk** and reduce treatment effectiveness. A targeted search for sleep apnea, COPD, or other hypoxic states is needed.
{% else %}
Possible causes:
- **Secondary**: chronic hypoxia (smoking, sleep apnea, lung disease, high altitude)
- **Relative**: dehydration (often falsely raises counts)
- **Primary**: polycythemia vera — a rare bone marrow disorder, more common after age 50
{% endif %}

{% if signals.thrombocytosis or signals.leukocytosis %}
Other blood cells are also elevated — this raises suspicion for true polycythemia. Important to clarify with your doctor, as treatment differs from secondary causes.
{% endif %}
---
actions:
{% if smoker %}
- **Consider quitting smoking** — the single most impactful change. Discuss nicotine replacement with your doctor.
- Get pulse oximetry / oxygen saturation — to rule out other hypoxia causes
- Test ferritin — smoker erythrocytosis usually has normal JAK2
- Recheck CBC 3 months after quitting
- If you snore / have daytime sleepiness — get evaluated for sleep apnea
{% elif has_cardiovascular_disease %}
- **See a cardiologist promptly** — assess thrombosis risk, possibly adjust therapy
- Sleep apnea evaluation (common in CVD too)
- Test JAK2 — to rule out polycythemia vera
- Check overnight oxygen saturation
{% else %}
- See your GP — full clinical evaluation needed
- If you smoke — tell your doctor how often and how long
- Discuss sleep quality (apnea is a common cause)
- May need hematology consult and **JAK2** mutation testing
{% endif %}
---
red_flags:
- Headaches, dizziness, ringing in ears
- Facial flushing, itching after a shower
- Blurred vision, numbness in extremities
- Chest pain, shortness of breath
{% if smoker %}
- Severe shortness of breath with mild exertion — possible developing COPD
{% endif %}
