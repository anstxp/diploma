# Iron deficiency
icon: 🩸
severity: medium
---
{% if ferritin %}Your ferritin ({{ ferritin }} ng/mL){% else %}Your iron markers{% endif %} indicate **iron deficiency**. Ferritin is the best marker of body iron stores.{% if tsat %} Low TSAT ({{ tsat }}%) confirms it.{% endif %}

Iron deficiency develops when losses exceed intake:
{% if is_female and age and age < 50 %}
- In women of reproductive age — most often through **heavy or prolonged periods**
- Another common cause — inadequate dietary intake (especially vegetarian diets)
{% elif is_male or (age and age >= 50) %}
- In men and women over 50 — **the cause must always be investigated**
- Most often — hidden GI blood loss (ulcers, polyps, less often tumours)
- Second — inadequate iron absorption
{% endif %}

Symptoms: fatigue, exertional shortness of breath, pallor, brittle nails, hair loss, cold extremities.
{% if on_oral_anticoagulants %}

**Particularly important for you:** you're on anticoagulants. Iron deficiency combined with anticoagulants often indicates **hidden GI bleeding** — this requires urgent workup.
{% endif %}
---
actions:
- See a GP with these results
- Get a CBC to evaluate anemia
- {% if is_male or (age and age >= 50) %}**Discuss gastroscopy/colonoscopy** to rule out GI bleeding sources{% else %}If periods are heavy, discuss with a gynecologist{% endif %}
- Don't self-supplement iron — your doctor will prescribe dose and form
- Diet: red meat, liver, legumes, leafy greens with vitamin-C foods
- Avoid tea/coffee with meals (they reduce absorption)
{% if on_oral_anticoagulants %}- Do not adjust anticoagulant dose on your own — even temporarily{% endif %}
---
red_flags:
- Severe shortness of breath, palpitations, dizziness
- Black tarry stools or blood in stools — **see a doctor immediately**
- Blood in vomit
- Severe worsening fatigue
{% if on_oral_anticoagulants %}- Any new bleeding (nasal, gums, bruising) while on anticoagulants — see a doctor{% endif %}
