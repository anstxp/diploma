# Hepatocellular injury pattern
icon: 🟠
severity: medium
---
Your liver enzymes {% if alt %}ALT ({{ alt }} U/L){% endif %}{% if alt and ast %} and {% endif %}{% if ast %}AST ({{ ast }} U/L){% endif %} are elevated. This means liver cells are actively breaking down — enzymes leak into the blood. This pattern is called **hepatocellular injury**.

{% if has_liver_disease %}
You have known liver disease — current values need to be compared to your usual ones. If this is **a significant worsening**, see a hepatologist promptly. If within your range, this is part of monitoring.
{% elif on_statins %}
You're on statins — they cause **mild-to-moderate ALT/AST elevation in ~2% of patients**. Usually this is safe, doesn't require stopping, and often resolves on its own. **Don't stop statins on your own** — that raises MI risk.
{% elif has_diabetes %}
Diabetics often develop **non-alcoholic fatty liver disease (NAFLD)** — about 70% of T2DM patients. This is the most likely cause in your case, especially if overweight.
{% else %}
Most common causes:
- **Fatty liver disease (NAFLD)** — especially with overweight, diabetes
- **Viral hepatitis** (B, C) — must be ruled out
- **Toxic injury** — alcohol, certain meds (high-dose acetaminophen, statins, amoxicillin-clavulanate)
- Less common — autoimmune hepatitis
{% endif %}
---
actions:
{% if has_liver_disease %}
- **Show results to your hepatologist** — compare to your usual trend
- Verify all prescribed medications are taken regularly
- Alcohol abstinence is critical
- Liver ultrasound if not done recently
{% elif on_statins %}
- **Don't stop statins on your own** — discuss with your doctor
- If ALT <3× upper limit — statins are usually safe
- If ALT ≥3× upper limit — your doctor may temporarily reduce dose or switch statin
- Test in 4 weeks: ALT, AST, GGT, CK (creatine kinase) — to rule out rhabdomyolysis
{% elif has_diabetes %}
- See an endocrinologist or gastroenterologist
- Get tested: HBsAg, anti-HCV (rule out viral), repeat ALT/AST
- Liver ultrasound — assess fatty liver
- Control HbA1c and weight — foundation of NAFLD treatment
- Avoid alcohol
{% else %}
- See a GP or gastroenterologist
- Get tested: HBsAg, anti-HCV (viral hepatitis), repeat ALT/AST in 4 weeks
- If AST/ALT > 2 — rule out alcohol misuse
- Limit alcohol to **complete abstinence** until next labs
- Review medications with your doctor
- Liver ultrasound to assess structure
{% endif %}
---
red_flags:
- Yellowing of skin or eyes (jaundice)
- Dark urine or pale stool
- Severe itching
- Right upper quadrant pain
- Confusion — **emergency**
{% if on_statins %}
- Severe muscle pain or dark urine — **possible statin-induced rhabdomyolysis** — see a doctor urgently
{% endif %}
