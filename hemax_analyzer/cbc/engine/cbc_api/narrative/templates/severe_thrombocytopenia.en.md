# Critically low platelets — increased bleeding risk
icon: 🔴
severity: high
---
Your platelet count ({{ plt }} ×10⁹/L) is very low. Platelets are responsible for blood clotting, and at these levels there's a risk of **spontaneous bleeding** — from gums, nose, or after minor trauma.

{% if on_oral_anticoagulants %}
**WARNING — YOU'RE ON ANTICOAGULANTS.** The combination of low platelets and anticoagulant therapy **dramatically increases the risk of dangerous bleeds** — intracranial, GI, intra-articular. This is **an emergency** requiring urgent consultation.
{% elif on_corticosteroids %}
You're on corticosteroids — they affect platelets unpredictably. Long-term high-dose steroids can paradoxically lower platelets. Your doctor needs to evaluate whether this relates to your therapy.
{% elif has_liver_disease %}
You have liver disease — this is a **very common cause of thrombocytopenia**. The liver produces thrombopoietin, and the spleen sequesters platelets in cirrhosis. Current values are critically low — a liver assessment is needed.
{% else %}
Causes: drug side effects, viral infections, immune thrombocytopenia (ITP), liver disease, splenic disorders, or bone marrow disease.
{% endif %}
---
actions:
{% if on_oral_anticoagulants %}
- **URGENT — go to the ER today.** Don't wait until tomorrow.
- **Don't stop the anticoagulant on your own** — that risks thrombosis. The doctor will decide.
- Avoid any trauma, don't take other medications without coordination
- Bring a list of all medications and doses
- If there's any bleeding — that's critical, mention it immediately
{% else %}
- **See a doctor today** — you need a GP and likely hematology consult
- Avoid trauma, contact sports, falls
- Don't take **aspirin, ibuprofen** or similar — they impair clotting
- Tell your doctor about all medications you take
{% endif %}
---
red_flags:
- Tiny red dots on skin (petechiae) or large bruises without cause
- Bleeding gums, nosebleeds, prolonged bleeding from cuts
- Blood in urine, stool, or vomit — **emergency**
- Severe headache, sudden one-sided weakness — emergency
{% if on_oral_anticoagulants %}
- Any new bleeding on anticoagulants — **emergency**
- Severe abdominal or back pain — possible internal bleeding
{% endif %}
