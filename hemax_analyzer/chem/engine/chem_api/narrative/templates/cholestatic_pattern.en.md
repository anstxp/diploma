# Cholestatic pattern — bile flow obstruction
icon: 🟠
severity: medium
---
Your enzymes **{% if alp %}ALP ({{ alp }} U/L){% endif %}{% if alp and ggt %} and {% endif %}{% if ggt %}GGT ({{ ggt }} U/L){% endif %}** are elevated, while ALT/AST are normal or only slightly elevated. This is a **cholestatic picture** — impaired bile flow.

{% if pregnant %}
**Mild-to-moderate ALP elevation in pregnancy is physiological** — the placenta makes its own ALP isoenzyme. So this result alone often doesn't mean pathology. But if ALP rose sharply, or rises with GGT and itching, it could be **cholestasis of pregnancy**, which needs monitoring.
{% elif on_oral_anticoagulants %}
You're on anticoagulants — some (especially warfarin, less so DOACs) can cause **drug-induced cholestasis**. This needs to be sorted out — the drug may need substituting.
{% elif has_liver_disease %}
You have known liver disease — this picture may signal progression or a new problem (e.g., biliary obstruction). See a hepatologist promptly.
{% else %}
Possible causes:
- **Gallstones** — duct obstruction
- **Drug-induced cholestasis** — certain medications
- **Primary biliary cholangitis** (PBC) — more common in women
- Isolated GGT — often alcohol
- Less commonly — tumors
{% endif %}
---
actions:
{% if pregnant %}
- **Discuss with your OB-GYN** — pregnancy needs more careful evaluation
- If you have itching (especially palms and soles), test **serum bile acids** for cholestasis of pregnancy
- Liver ultrasound — safe in pregnancy
- Don't take any medications without your doctor's input
{% elif on_oral_anticoagulants %}
- **See the doctor who prescribed the anticoagulant** — discuss substitution
- Don't stop the drug on your own — increases thrombosis risk
- Test: repeat ALP/GGT in 2-4 weeks after change, liver ultrasound
- Review other medications — others may be culprits too
{% else %}
- See a gastroenterologist
- Get tested: repeat ALP/GGT, **liver and biliary ultrasound**, bilirubin
- If isolated GGT — review alcohol intake
- Review medications with your doctor
- Next tests (as ordered): MRCP or CT if biliary obstruction is suspected
{% endif %}
---
red_flags:
- Generalized itching
- Yellowing of skin/eyes
- Right upper quadrant pain, especially after fatty foods
- Pale stools, dark urine
- Fever with chills
{% if pregnant %}
- Severe palm/sole itching at night — suspect cholestasis of pregnancy, **see OB ASAP**
- Decreased fetal movements — see OB urgently
{% endif %}
