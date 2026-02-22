# Critically low neutrophils — increased infection risk
icon: 🔴
severity: high
---
Your neutrophil count ({{ anc }} ×10⁹/L) is significantly low. Neutrophils are your main defense against bacterial and fungal infections. At these levels, infections can develop **rapidly and severely**, even from minor causes.

{% if takes_chemotherapy %}
**This is an expected effect of chemotherapy** — drugs suppress the bone marrow. But **expected ≠ safe**: febrile neutropenia (fever + low neutrophils) remains life-threatening.

Any temperature ≥38°C at this stage = **call EMS or go to ER immediately**, no exceptions. Don't take acetaminophen "just to bring it down and see" — that masks the signal. Most cancer centers have a direct hotline for these situations.
{% elif on_corticosteroids %}
Steroids usually **raise** neutrophils, not lower them. Such a drop on steroids is unusual — needs evaluation for other causes (viral infection, drug interaction).
{% elif has_autoimmune %}
You have autoimmune disease — neutropenia can be a manifestation of the disease itself (especially in lupus) or a side effect of therapy (methotrexate, azathioprine). Rheumatology evaluation needed.
{% else %}
Causes vary: drug side effects (especially chemo, some antibiotics, antipsychotics), viral infections, autoimmune disease, bone marrow disorders.
{% endif %}
---
actions:
{% if takes_chemotherapy %}
- **Any temperature ≥38°C — GO TO ER IMMEDIATELY** (febrile neutropenia is an emergency)
- Contact your oncologist today to discuss current values
- Avoid crowds, sick contacts, raw food (vegetables/fish/meat)
- Strict hygiene: hand washing, oral care, nail care
- Discuss G-CSF (filgrastim) with your oncologist — stimulates neutrophils
- Keep your cancer center's emergency number at hand
{% elif on_corticosteroids %}
- **See a doctor today** — this drop on steroids is atypical
- Get tested: viral markers (CMV, EBV), repeat CBC
- Don't stop steroids on your own — separate danger
{% elif has_autoimmune %}
- **See a rheumatologist** with these results
- Review all your medications — some can cause neutropenia
- Avoid infectious contacts until therapy is reviewed
{% else %}
- **Contact your doctor immediately** (today)
- If you've recently started new medications — tell them
- Until consultation: avoid crowds, don't prepare raw food for others, wash hands carefully
- Standard preventive measures aren't enough — see a doctor
{% endif %}
---
red_flags:
- Temperature above 38°C — **go to ER immediately**, don't wait
- Chills, sweats, feeling severely ill
- Pain or redness anywhere — possible local infection
{% if takes_chemotherapy %}
- Sore throat, painful swallowing, mouth ulcers — mucositis with overlying infection
- Any bleeding — chemo often causes concurrent thrombocytopenia
{% endif %}
