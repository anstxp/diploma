# Incomplete panel
icon: ⚠️
severity: low
---
You've provided fewer than {{ n_features_provided }} measurements — for full 6-risk assessment, the model needs at least 15 features (CBC + CHEM + basic anthropometric).

The current prediction is likely imprecise — the model is filling in missing values with population averages.
---
actions:
- Get full CBC + basic biochemistry (HbA1c, glucose, creatinine, lipids, ALT)
- Measure blood pressure
- Provide height and weight for BMI
- Then re-run risk analysis
---
red_flags: 
