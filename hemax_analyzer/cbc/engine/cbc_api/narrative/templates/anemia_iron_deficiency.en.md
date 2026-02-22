# Signs of iron deficiency
icon: 🩸
severity: medium
---
Your hemoglobin — {{ hgb }} g/dL — is {% if hgb_low %}below the lower limit ({{ hgb_low }}){% else %}low{% endif %}. Your red cells are also smaller and contain less hemoglobin than expected — this is the classic picture of **iron deficiency**.

{% if pregnant %}
Iron requirements rise during pregnancy — both for the baby and for the expanded blood volume. Iron deficiency is very common in pregnancy and **shouldn't be ignored** — it raises the risk of preterm delivery and affects fetal development. Iron supplements are safe and often necessary.
{% elif on_oral_anticoagulants %}
You're on anticoagulants — iron deficiency is **especially concerning** here. Hidden bleeding (often GI) must be actively investigated. Patients on warfarin/DOACs have a higher risk of occult GI hemorrhage.
{% elif has_ckd %}
You have chronic kidney disease — kidneys produce erythropoietin, the hormone that drives red cell production. Anemia in CKD isn't always plain iron deficiency. A full iron panel (ferritin + transferrin saturation) is needed to differentiate.
{% elif is_female and age and age < 50 %}
In women of reproductive age, the most common cause is **blood loss from heavy or prolonged periods**. The next is dietary deficiency (especially in vegetarian diets).
{% elif is_male or (age and age >= 50) %}
In men and women over 50, iron deficiency **always requires a cause search** — usually occult GI blood loss (ulcers, polyps, less commonly tumors). The cause must be actively pursued.
{% elif age and age < 18 %}
At your age, iron deficiency is often related to rapid growth and inadequate dietary intake. But other causes still need to be ruled out.
{% endif %}

It's not possible to determine the specific cause from this CBC alone — additional tests are needed.
---
actions:
- Get additional tests: **ferritin** (most informative), serum iron, transferrin, TIBC
{% if has_ckd %}
- Also test creatinine, eGFR, urine albumin/creatinine ratio — to assess CKD stage and erythropoietin needs
- See a nephrologist — anemia in CKD may need specialized treatment (erythropoietin, IV iron)
{% elif on_oral_anticoagulants %}
- Discuss urgently with your doctor — endoscopy/colonoscopy may be needed to find the source
- Don't change anticoagulant dose on your own
{% elif pregnant %}
- Discuss safe iron supplementation with your OB-GYN
- Hemoglobin re-check every 4-6 weeks
{% else %}
- See your GP with these results
- {% if is_male or (age and age >= 50) %}Discuss the need for endoscopy / colonoscopy with your doctor to find the bleeding source{% else %}If your periods are heavy — discuss with a gynecologist{% endif %}
{% endif %}
- Don't start iron supplements on your own — iron overload is also harmful
- Diet: red meat, liver, beans, leafy greens; eat them with vitamin-C-rich foods (citrus, peppers); avoid tea/coffee with meals (they impair iron absorption)
---
red_flags:
- Shortness of breath at rest, chest pain, or palpitations
- Dizziness on standing, near-fainting episodes
- Black, tarry stools or blood in stool — **see a doctor immediately**
- Blood in vomit
{% if on_oral_anticoagulants %}
- Any new bleeding (nose, gums, bruising) on anticoagulants — see a doctor urgently
{% endif %}
