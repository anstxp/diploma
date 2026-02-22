# Anemia with large red cells — likely B12 or folate deficiency
icon: 🩸
severity: medium
---
Your hemoglobin is low and your red cells are **larger than normal** (MCV = {{ mcv }} fL). This pattern usually points to **vitamin B12** or **folate** deficiency — both are required for normal red-cell maturation in the bone marrow.

{% if has_diabetes and on_oral_diabetics %}
You're on oral diabetes medication — most often **metformin**. **Long-term metformin (5+ years) reduces B12 absorption in ~30% of patients** by affecting the small intestine. This is the most likely cause in your case. Good news: B12 deficiency is easily treated with injections or high-dose oral supplements.
{% elif age and age >= 65 %}
At your age B12 deficiency is more common — about 10-15% of people over 65 have impaired B12 absorption (atrophic gastritis). Long-term replacement is often needed.
{% elif on_oral_anticoagulants %}
You're on anticoagulants — even minor bleeding becomes dangerous, but it's not usually the main cause of macrocytic anemia. Still, occult blood loss should be ruled out.
{% else %}
Other possible causes: regular alcohol use, certain medications (long-term metformin, methotrexate), thyroid disease. Less commonly — bone marrow disorders.
{% endif %}
---
actions:
- Get tested: **vitamin B12**, **folate** (serum), TSH (thyroid), ideally homocysteine
{% if has_diabetes and on_oral_diabetics %}
- Tell your endocrinologist — patients on metformin are often advised to check B12 yearly
- If B12 is truly low — treat with injections (1000 mcg/month) or high-dose oral
- Don't stop metformin on your own — treating B12 deficiency doesn't require it
{% else %}
- See your GP with these results
- If you drink alcohol regularly — that's important info for your doctor
- List all medications including supplements
{% endif %}
---
red_flags:
- Numbness or tingling in hands/feet
- Balance or memory problems
- Burning tongue or color change
- Pale skin with yellowish tint
{% if has_diabetes %}
- Tingling in feet can be confused with diabetic neuropathy — checking B12 is essential to not miss it
{% endif %}
