# Low magnesium
icon: 🦴
severity: low
---
Your magnesium ({{ magnesium }} mg/dL) is below normal. Magnesium deficiency often accompanies hypokalemia and hypocalcemia (the latter can't be corrected without first correcting magnesium).

{% if on_diuretics %}
**Most likely cause — diuretics**, especially loop diuretics (furosemide, torasemide) and thiazides. They actively waste magnesium in the urine. Most patients on diuretics need periodic magnesium supplementation.
{% elif on_oral_diabetics %}
In patients on oral diabetes medications (especially metformin), magnesium often drops due to reduced gut absorption and increased urinary loss with glycosuria.
{% elif has_liver_disease %}
In liver disease (especially in chronic alcohol use), magnesium deficiency is common and can worsen the overall state.
{% else %}
Causes: dietary deficiency, malabsorption, prolonged diarrhea, diuretics or proton-pump inhibitors (PPIs), chronic alcohol use.
{% endif %}
---
actions:
{% if on_diuretics %}
- Discuss with your doctor — oral magnesium (e.g., magnesium citrate) may be needed, or diuretic adjustment
- Test: potassium, calcium (often all three are low together)
- Don't stop the diuretic on your own
- Diet: more nuts, seeds, dark leafy greens, dark chocolate
{% elif has_liver_disease %}
- See a gastroenterologist — magnesium plus zinc supplementation often needed
- If you drink alcohol — full abstinence improves many parameters
- Test: potassium, calcium, phosphorus
{% else %}
- Get tested: potassium, calcium, creatinine
- Review medications with your doctor (especially PPIs — omeprazole, pantoprazole)
- Eat more nuts, seeds, dark leafy greens, chocolate
- If significantly deficient, your doctor will prescribe magnesium supplements
- Don't take large doses on your own with CKD
{% endif %}
---
red_flags:
- Muscle cramps, twitching
- Palpitations, arrhythmia
- Weakness
- Tremor
{% if on_diuretics %}
- Palpitations + weakness on loop diuretics — check potassium and magnesium together
{% endif %}
