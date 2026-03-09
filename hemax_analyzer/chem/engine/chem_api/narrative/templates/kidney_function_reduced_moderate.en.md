# Reduced kidney function
icon: 🫘
severity: medium
---
Your eGFR ({{ egfr }} mL/min/1.73m²) is reduced and creatinine ({{ creatinine }} mg/dL) is elevated. These are signs of **early-to-moderate chronic kidney disease (CKD)**.

{% if has_ckd %}
Your profile already lists CKD — these numbers let us track the trend. If this is **a worsening from your usual values**, an unscheduled nephrology visit is warranted. If within your stable range, this is part of monitoring.
{% elif has_diabetes %}
You have diabetes, so this is most likely **diabetic nephropathy** — diabetes' most common complication. Good news: at this stage it can be stabilized with aggressive glucose and BP control. Tighter targets often needed: HbA1c <7%, BP <130/80 mmHg.
{% elif has_hypertension %}
You have hypertension — the second most common cause of CKD (after diabetes). BP control <130/80 is critical to prevent progression.
{% elif on_acei_arb %}
You're on an ACE inhibitor / ARB — these drugs **protect kidneys** in CKD, but can cause a small creatinine rise (up to 30%) when starting therapy. This is **expected and not a reason to stop**. But it's important to confirm this isn't acute worsening.
{% else %}
CKD is most often caused by diabetes, hypertension, long-term medication use (e.g., NSAIDs), aging changes. At this stage full recovery is possible with cause removal — or at least progression can be halted.
{% endif %}
---
actions:
{% if has_ckd %}
- **Show results to your nephrologist** — compare to your usual trend
- Verify all prescribed meds are taken (ACE-I/ARB, statins)
- Avoid NSAIDs (ibuprofen, diclofenac) — they harm even healthy kidneys
- Home BP monitoring — target <130/80
- Check serum potassium if on ACE-I/ARB or K-sparing diuretics
{% elif has_diabetes %}
- **See an endocrinologist and nephrologist** — diabetic nephropathy needs specialized care
- Get tested: HbA1c, urine microalbumin (albumin/creatinine ratio), repeat creatinine
- Discuss starting an ACE inhibitor / ARB — they protect kidneys even at normal BP in diabetics
- Tighter targets: HbA1c <7%, BP <130/80
- Review metformin dose with your doctor (low GFR needs adjustment)
{% elif has_hypertension %}
- **BP control is the top priority.** Target BP <130/80 mmHg.
- Get tested: urine microalbumin, repeat creatinine in a month
- Discuss ACE inhibitor or ARB with your doctor — lower BP and protect kidneys
- Avoid NSAIDs (ibuprofen/diclofenac) — worsen both BP and kidneys
{% elif on_acei_arb %}
- Show results to the doctor who prescribed the ACE-I/ARB
- Test serum potassium — ACE-I can raise it in CKD
- **Don't stop the drug on your own** — that may harm more than the small creatinine rise
- Recheck creatinine in 2-4 weeks to see the trend
{% else %}
- See a GP or internist to establish the cause
- Get tested: repeat creatinine, urine protein, urine albumin/creatinine ratio
- Check BP and glucose — most common CKD causes
- Avoid regular **ibuprofen, diclofenac**, other NSAIDs
- Drink enough water but not excessive
- Recheck the test in 3 months
{% endif %}
---
red_flags:
- New swelling
- Decreased urine output
- Blood in urine (pink or brown)
- Persistent fatigue, weakness
{% if on_acei_arb %}
- Dry cough — common ACE-I side effect, discuss switching to ARB
- Muscle weakness, irregular heartbeat — possible hyperkalemia from ACE-I
{% endif %}
