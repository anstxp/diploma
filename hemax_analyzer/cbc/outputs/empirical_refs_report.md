# Empirical CBC Reference Intervals — NHANES Healthy Cohort

**Methodology.** Non-parametric reference intervals (2.5th and 97.5th percentiles) were derived from a healthy reference population drawn from the harmonised NHANES 1999–2023 master dataset, following the Clinical and Laboratory Standards Institute document EP28-A3c. Within each partition, Tukey-fence outliers (1.5 × IQR) were removed prior to percentile estimation. Ninety-percent confidence intervals for each reference limit were obtained by non-parametric bootstrap (R = 1000 resamples with replacement). Partitioning of the reference population by sex and by age band was evaluated using the Harris-Boyd z-statistic z = |μ₁ − μ₂| / √(s₁²/n₁ + s₂²/n₂) with a critical value of 3 × √(n̄/120); partitioning was considered statistically justified when |z| exceeded that threshold.

**Inclusion criteria (healthy cohort).** Adults aged 20–80 (age bands: 20–40, 40–60, 60–80), not pregnant, body-mass index 18.5–30 kg/m², no self-reported history of cardiovascular disease, diabetes, hypertension, chronic kidney disease, cancer, liver or thyroid disease, no anti-hypertensive / lipid-lowering / glucose-lowering medications, and companion lipid, glycaemic, renal and hepatic indices within conventional normal ranges.

**Reference population size:** 9,413 participants (from 119,555 available in the master NHANES dataset).

---

## 1. Summary — empirical vs textbook intervals

Intervals shown are pooled across the age bands within each sex, with sex collapsed to a single interval only when Harris-Boyd testing showed no justification for a sex partition at any age.

| Biomarker | Unit | Textbook ♀ | Empirical ♀ | Textbook ♂ | Empirical ♂ | Partitioning |
|---|---|---|---|---|---|---|
| WBC (leukocytes) | ×10⁹/L | 4–11 | 3.21–10.80 | 4–11 | 3.62–10.60 | collapsed |
| Neutrophils % | % | 45–75 | 39.31–74.00 | 45–75 | 38.49–75.14 | collapsed |
| Lymphocytes % | % | 20–45 | 17.06–47.20 | 20–45 | 15.22–47.33 | sex |
| Monocytes % | % | 2–10 | 4.30–11.56 | 2–10 | 4.60–12.98 | sex |
| Eosinophils % | % | 0.5–5 | 0.49–5.41 | 0.5–5 | 0.60–6.39 | sex |
| Basophils % | % | 0–1.5 | 0.10–1.38 | 0–1.5 | 0.10–1.30 | collapsed |
| Neutrophils abs. (ANC) | ×10⁹/L | 1.5–7.5 | 1.40–7.00 | 1.5–7.5 | 1.60–6.80 | collapsed |
| Lymphocytes abs. (ALC) | ×10⁹/L | 1–4 | 1.00–3.30 | 1–4 | 0.90–3.20 | collapsed |
| Monocytes abs. | ×10⁹/L | 0.2–0.8 | 0.20–0.80 | 0.2–0.8 | 0.30–0.90 | sex |
| Eosinophils abs. | ×10⁹/L | 0–0.5 | 0.00–0.30 | 0–0.5 | 0.00–0.50 | sex |
| Basophils abs. | ×10⁹/L | 0–0.1 | 0.00–0.10 | 0–0.1 | 0.00–0.10 | collapsed |
| RBC | ×10¹²/L | 3.8–5.2 | 3.78–5.05 | 4.2–5.8 | 3.98–5.78 | sex |
| Hemoglobin | g/dL | 12–16 | 11.30–15.48 | 13–17.5 | 12.81–17.20 | sex |
| Hematocrit | % | 35–47 | 33.70–45.36 | 41–53 | 38.00–50.70 | sex |
| MCV | fL | 80–100 | 80.50–99.57 | 80–100 | 82.30–99.80 | collapsed |
| MCH | pg | 27–33 | 26.70–34.00 | 27–33 | 27.40–34.50 | collapsed |
| MCHC | g/dL | 31.5–36.5 | 32.10–35.60 | 31.5–36.5 | 32.40–35.68 | collapsed |
| RDW | % | 11.5–15 | 11.30–14.70 | 11.5–15 | 11.40–14.50 | collapsed |
| Platelets | ×10⁹/L | 150–450 | 150.20–379.00 | 150–450 | 131.60–346.25 | sex |
| MPV | fL | 7–11.5 | 6.60–10.10 | 7–11.5 | 6.42–9.90 | collapsed |

---

## 2. Per-biomarker tables

### 2.1 WBC (leukocytes) (×10⁹/L) — code `wbc`

*Textbook:* ♀ 4–11, ♂ 4–11

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3267 | 55 | 3212 | 6.80 | 4.00 | 10.80 | [3.90, 4.10] | [10.70, 10.97] |
| ♀ 40 60 | 1501 | 19 | 1482 | 6.40 | 3.70 | 10.30 | [3.50, 3.80] | [10.00, 10.50] |
| ♀ 60 80 | 293 | 10 | 283 | 5.80 | 3.21 | 8.40 | [3.10, 3.50] | [8.10, 9.00] |
| ♂ 20 40 | 2832 | 42 | 2790 | 6.50 | 3.80 | 10.60 | [3.70, 3.90] | [10.40, 10.80] |
| ♂ 40 60 | 1171 | 35 | 1136 | 6.40 | 3.80 | 10.20 | [3.50, 3.90] | [10.00, 10.40] |
| ♂ 60 80 | 334 | 7 | 327 | 6.00 | 3.62 | 10.20 | [3.40, 3.80] | [9.70, 10.60] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 4.85, z_crit = 15.00 → not justified (collapse)
- 40_60: z = 0.85, z_crit = 9.91 → not justified (collapse)
- 60_80: z = 4.15, z_crit = 4.78 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 7.22, z_crit = 13.27 → not justified
- female, 40-60 vs 60-80: z = 7.38, z_crit = 8.14 → not justified
- male, 20-40 vs 40-60: z = 1.88, z_crit = 12.13 → not justified
- male, 40-60 vs 60-80: z = 1.98, z_crit = 7.41 → not justified

---

### 2.2 Neutrophils % (%) — code `neut_pct`

*Textbook:* ♀ 45–75, ♂ 45–75

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3264 | 29 | 3235 | 58.00 | 40.10 | 73.80 | [39.50, 40.48] | [73.22, 74.40] |
| ♀ 40 60 | 1499 | 24 | 1475 | 58.50 | 41.40 | 74.00 | [40.30, 42.17] | [73.40, 74.24] |
| ♀ 60 80 | 293 | 7 | 286 | 57.00 | 39.31 | 71.62 | [38.20, 41.30] | [69.89, 73.70] |
| ♂ 20 40 | 2831 | 34 | 2797 | 56.50 | 38.49 | 73.30 | [37.60, 39.20] | [72.71, 74.12] |
| ♂ 40 60 | 1171 | 21 | 1150 | 57.50 | 41.47 | 73.05 | [40.70, 42.47] | [72.45, 74.63] |
| ♂ 60 80 | 334 | 5 | 329 | 59.20 | 40.40 | 75.14 | [37.62, 42.12] | [73.50, 77.94] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 5.77, z_crit = 15.04 → not justified (collapse)
- 40_60: z = 2.12, z_crit = 9.92 → not justified (collapse)
- 60_80: z = 2.99, z_crit = 4.80 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 3.18, z_crit = 13.29 → not justified
- female, 40-60 vs 60-80: z = 3.36, z_crit = 8.13 → not justified
- male, 20-40 vs 40-60: z = 4.88, z_crit = 12.17 → not justified
- male, 40-60 vs 60-80: z = 1.78, z_crit = 7.45 → not justified

---

### 2.3 Lymphocytes % (%) — code `lymph_pct`

*Textbook:* ♀ 20–45, ♂ 20–45

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3264 | 38 | 3226 | 31.30 | 18.30 | 47.20 | [17.66, 18.70] | [46.60, 47.80] |
| ♀ 40 60 | 1499 | 34 | 1465 | 30.50 | 17.06 | 46.28 | [16.50, 17.70] | [44.70, 47.00] |
| ♀ 60 80 | 293 | 7 | 286 | 31.90 | 18.85 | 46.09 | [16.56, 20.01] | [45.10, 47.30] |
| ♂ 20 40 | 2831 | 42 | 2789 | 31.40 | 17.00 | 47.33 | [16.50, 17.80] | [46.60, 47.83] |
| ♂ 40 60 | 1171 | 15 | 1156 | 29.90 | 16.20 | 45.50 | [15.30, 17.16] | [44.82, 46.41] |
| ♂ 60 80 | 334 | 3 | 331 | 28.50 | 15.22 | 46.70 | [13.53, 16.28] | [44.80, 48.50] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 0.25, z_crit = 15.02 → not justified (collapse)
- 40_60: z = 1.27, z_crit = 9.91 → not justified (collapse)
- 60_80: z = 5.07, z_crit = 4.81 → **partition justified**

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 4.39, z_crit = 13.26 → not justified
- female, 40-60 vs 60-80: z = 2.69, z_crit = 8.10 → not justified
- male, 20-40 vs 40-60: z = 5.05, z_crit = 12.16 → not justified
- male, 40-60 vs 60-80: z = 3.04, z_crit = 7.47 → not justified

---

### 2.4 Monocytes % (%) — code `mono_pct`

*Textbook:* ♀ 2–10, ♂ 2–10

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3264 | 90 | 3174 | 7.10 | 4.30 | 10.90 | [4.20, 4.40] | [10.70, 11.00] |
| ♀ 40 60 | 1499 | 27 | 1472 | 7.30 | 4.30 | 11.22 | [4.10, 4.40] | [11.00, 11.42] |
| ♀ 60 80 | 293 | 5 | 288 | 7.80 | 5.00 | 11.56 | [4.47, 5.20] | [11.28, 12.58] |
| ♂ 20 40 | 2830 | 67 | 2763 | 8.10 | 4.70 | 12.20 | [4.60, 4.80] | [12.00, 12.40] |
| ♂ 40 60 | 1171 | 20 | 1151 | 8.00 | 4.60 | 12.20 | [4.40, 4.88] | [12.00, 12.43] |
| ♂ 60 80 | 334 | 9 | 325 | 8.40 | 4.60 | 12.98 | [4.33, 4.91] | [12.18, 13.59] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 20.24, z_crit = 14.92 → **partition justified**
- 40_60: z = 9.38, z_crit = 9.92 → not justified (collapse)
- 60_80: z = 3.84, z_crit = 4.79 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 2.85, z_crit = 13.20 → not justified
- female, 40-60 vs 60-80: z = 4.55, z_crit = 8.12 → not justified
- male, 20-40 vs 40-60: z = 1.64, z_crit = 12.12 → not justified
- male, 40-60 vs 60-80: z = 3.53, z_crit = 7.44 → not justified

---

### 2.5 Eosinophils % (%) — code `eos_pct`

*Textbook:* ♀ 0.5–5, ♂ 0.5–5

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3263 | 206 | 3057 | 1.80 | 0.50 | 5.16 | [0.50, 0.50] | [5.10, 5.30] |
| ♀ 40 60 | 1499 | 84 | 1415 | 1.90 | 0.60 | 4.90 | [0.50, 0.60] | [4.70, 5.10] |
| ♀ 60 80 | 293 | 15 | 278 | 2.00 | 0.49 | 5.41 | [0.20, 0.69] | [4.80, 5.90] |
| ♂ 20 40 | 2831 | 147 | 2684 | 2.20 | 0.60 | 6.30 | [0.60, 0.60] | [6.20, 6.40] |
| ♂ 40 60 | 1171 | 67 | 1104 | 2.30 | 0.60 | 5.80 | [0.60, 0.60] | [5.60, 6.00] |
| ♂ 60 80 | 334 | 10 | 324 | 2.50 | 0.60 | 6.39 | [0.41, 0.80] | [6.10, 6.98] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 11.88, z_crit = 14.67 → not justified (collapse)
- 40_60: z = 7.81, z_crit = 9.72 → not justified (collapse)
- 60_80: z = 4.89, z_crit = 4.75 → **partition justified**

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 0.44, z_crit = 12.95 → not justified
- female, 40-60 vs 60-80: z = 1.77, z_crit = 7.97 → not justified
- male, 20-40 vs 40-60: z = 0.21, z_crit = 11.92 → not justified
- male, 40-60 vs 60-80: z = 3.12, z_crit = 7.32 → not justified

---

### 2.6 Basophils % (%) — code `baso_pct`

*Textbook:* ♀ 0–1.5, ♂ 0–1.5

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3264 | 98 | 3166 | 0.60 | 0.10 | 1.30 | [0.10, 0.10] | [1.30, 1.30] |
| ♀ 40 60 | 1499 | 50 | 1449 | 0.60 | 0.10 | 1.38 | [0.10, 0.12] | [1.30, 1.40] |
| ♀ 60 80 | 293 | 5 | 288 | 0.70 | 0.10 | 1.30 | [0.10, 0.30] | [1.30, 1.40] |
| ♂ 20 40 | 2831 | 86 | 2745 | 0.60 | 0.10 | 1.30 | [0.10, 0.10] | [1.30, 1.40] |
| ♂ 40 60 | 1171 | 35 | 1136 | 0.60 | 0.10 | 1.30 | [0.10, 0.10] | [1.30, 1.40] |
| ♂ 60 80 | 334 | 14 | 320 | 0.60 | 0.10 | 1.30 | [0.00, 0.20] | [1.30, 1.30] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 0.68, z_crit = 14.89 → not justified (collapse)
- 40_60: z = 0.89, z_crit = 9.85 → not justified (collapse)
- 60_80: z = 2.69, z_crit = 4.77 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 4.40, z_crit = 13.16 → not justified
- female, 40-60 vs 60-80: z = 3.68, z_crit = 8.07 → not justified
- male, 20-40 vs 40-60: z = 2.27, z_crit = 12.06 → not justified
- male, 40-60 vs 60-80: z = 0.90, z_crit = 7.39 → not justified

---

### 2.7 Neutrophils abs. (ANC) (×10⁹/L) — code `neut_abs`

*Textbook:* ♀ 1.5–7.5, ♂ 1.5–7.5

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3264 | 82 | 3182 | 3.90 | 1.80 | 7.00 | [1.70, 1.80] | [6.90, 7.10] |
| ♀ 40 60 | 1499 | 39 | 1460 | 3.70 | 1.70 | 6.60 | [1.60, 1.80] | [6.40, 6.70] |
| ♀ 60 80 | 293 | 8 | 285 | 3.30 | 1.40 | 5.49 | [1.30, 1.60] | [5.20, 5.70] |
| ♂ 20 40 | 2831 | 63 | 2768 | 3.60 | 1.60 | 6.80 | [1.50, 1.70] | [6.70, 6.90] |
| ♂ 40 60 | 1171 | 38 | 1133 | 3.70 | 1.60 | 6.80 | [1.50, 1.80] | [6.50, 6.90] |
| ♂ 60 80 | 334 | 8 | 326 | 3.60 | 1.71 | 6.60 | [1.52, 1.90] | [6.40, 7.09] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 5.73, z_crit = 14.94 → not justified (collapse)
- 40_60: z = 0.34, z_crit = 9.86 → not justified (collapse)
- 60_80: z = 4.45, z_crit = 4.79 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 5.04, z_crit = 13.19 → not justified
- female, 40-60 vs 60-80: z = 6.59, z_crit = 8.09 → not justified
- male, 20-40 vs 40-60: z = 0.30, z_crit = 12.09 → not justified
- male, 40-60 vs 60-80: z = 0.63, z_crit = 7.40 → not justified

---

### 2.8 Lymphocytes abs. (ALC) (×10⁹/L) — code `lymph_abs`

*Textbook:* ♀ 1–4, ♂ 1–4

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3264 | 59 | 3205 | 2.10 | 1.20 | 3.30 | [1.20, 1.20] | [3.30, 3.40] |
| ♀ 40 60 | 1499 | 44 | 1455 | 1.90 | 1.10 | 3.20 | [1.00, 1.10] | [3.10, 3.20] |
| ♀ 60 80 | 293 | 7 | 286 | 1.80 | 1.00 | 3.00 | [0.90, 1.10] | [2.80, 3.10] |
| ♂ 20 40 | 2831 | 72 | 2759 | 2.00 | 1.20 | 3.20 | [1.10, 1.20] | [3.10, 3.20] |
| ♂ 40 60 | 1171 | 25 | 1146 | 1.90 | 1.00 | 3.14 | [1.00, 1.10] | [3.10, 3.30] |
| ♂ 60 80 | 334 | 7 | 327 | 1.70 | 0.90 | 2.90 | [0.73, 1.00] | [2.78, 3.28] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 6.53, z_crit = 14.95 → not justified (collapse)
- 40_60: z = 0.57, z_crit = 9.88 → not justified (collapse)
- 60_80: z = 1.96, z_crit = 4.79 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 10.65, z_crit = 13.22 → not justified
- female, 40-60 vs 60-80: z = 2.67, z_crit = 8.08 → not justified
- male, 20-40 vs 40-60: z = 4.21, z_crit = 12.10 → not justified
- male, 40-60 vs 60-80: z = 5.37, z_crit = 7.43 → not justified

---

### 2.9 Monocytes abs. (×10⁹/L) — code `mono_abs`

*Textbook:* ♀ 0.2–0.8, ♂ 0.2–0.8

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3264 | 104 | 3160 | 0.50 | 0.30 | 0.80 | [0.30, 0.30] | [0.80, 0.80] |
| ♀ 40 60 | 1499 | 34 | 1465 | 0.50 | 0.20 | 0.80 | [0.20, 0.30] | [0.70, 0.80] |
| ♀ 60 80 | 293 | 4 | 289 | 0.50 | 0.30 | 0.70 | [0.22, 0.30] | [0.70, 0.80] |
| ♂ 20 40 | 2831 | 155 | 2676 | 0.50 | 0.30 | 0.80 | [0.30, 0.30] | [0.80, 0.80] |
| ♂ 40 60 | 1171 | 54 | 1117 | 0.50 | 0.30 | 0.80 | [0.30, 0.30] | [0.80, 0.80] |
| ♂ 60 80 | 334 | 4 | 330 | 0.50 | 0.30 | 0.90 | [0.22, 0.30] | [0.90, 1.00] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 9.64, z_crit = 14.79 → not justified (collapse)
- 40_60: z = 8.03, z_crit = 9.84 → not justified (collapse)
- 60_80: z = 6.24, z_crit = 4.82 → **partition justified**

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 4.42, z_crit = 13.17 → not justified
- female, 40-60 vs 60-80: z = 0.55, z_crit = 8.11 → not justified
- male, 20-40 vs 40-60: z = 1.99, z_crit = 11.93 → not justified
- male, 40-60 vs 60-80: z = 2.56, z_crit = 7.37 → not justified

---

### 2.10 Eosinophils abs. (×10⁹/L) — code `eos_abs`

*Textbook:* ♀ 0–0.5, ♂ 0–0.5

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3264 | 302 | 2962 | 0.10 | 0.00 | 0.30 | [0.00, 0.00] | [0.30, 0.30] |
| ♀ 40 60 | 1499 | 101 | 1398 | 0.10 | 0.00 | 0.30 | [0.00, 0.00] | [0.30, 0.30] |
| ♀ 60 80 | 293 | 18 | 275 | 0.10 | 0.00 | 0.30 | [0.00, 0.00] | [0.30, 0.30] |
| ♂ 20 40 | 2831 | 341 | 2490 | 0.10 | 0.00 | 0.30 | [0.00, 0.00] | [0.30, 0.30] |
| ♂ 40 60 | 1171 | 139 | 1032 | 0.10 | 0.00 | 0.30 | [0.00, 0.00] | [0.30, 0.30] |
| ♂ 60 80 | 334 | 4 | 330 | 0.20 | 0.00 | 0.50 | [0.00, 0.10] | [0.40, 0.50] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 5.45, z_crit = 14.30 → not justified (collapse)
- 40_60: z = 5.31, z_crit = 9.55 → not justified (collapse)
- 60_80: z = 7.15, z_crit = 4.76 → **partition justified**

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 0.92, z_crit = 12.79 → not justified
- female, 40-60 vs 60-80: z = 0.46, z_crit = 7.92 → not justified
- male, 20-40 vs 40-60: z = 1.10, z_crit = 11.49 → not justified
- male, 40-60 vs 60-80: z = 5.27, z_crit = 7.15 → not justified

---

### 2.11 Basophils abs. (×10⁹/L) — code `baso_abs`

*Textbook:* ♀ 0–0.1, ♂ 0–0.1

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3264 | 7 | 3257 | 0.00 | 0.00 | 0.10 | [0.00, 0.00] | [0.10, 0.10] |
| ♀ 40 60 | 1499 | 3 | 1496 | 0.00 | 0.00 | 0.10 | [0.00, 0.00] | [0.10, 0.10] |
| ♀ 60 80 | 293 | 1 | 292 | 0.00 | 0.00 | 0.10 | [0.00, 0.00] | [0.10, 0.10] |
| ♂ 20 40 | 2831 | 7 | 2824 | 0.00 | 0.00 | 0.10 | [0.00, 0.00] | [0.10, 0.10] |
| ♂ 40 60 | 1171 | 3 | 1168 | 0.00 | 0.00 | 0.10 | [0.00, 0.00] | [0.10, 0.10] |
| ♂ 60 80 | 334 | 1 | 333 | 0.00 | 0.00 | 0.10 | [0.00, 0.00] | [0.10, 0.10] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 1.33, z_crit = 15.10 → not justified (collapse)
- 40_60: z = 1.37, z_crit = 9.99 → not justified (collapse)
- 60_80: z = 0.11, z_crit = 4.84 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 0.35, z_crit = 13.35 → not justified
- female, 40-60 vs 60-80: z = 0.61, z_crit = 8.19 → not justified
- male, 20-40 vs 40-60: z = 2.17, z_crit = 12.24 → not justified
- male, 40-60 vs 60-80: z = 1.62, z_crit = 7.50 → not justified

---

### 2.12 RBC (×10¹²/L) — code `rbc`

*Textbook:* ♀ 3.8–5.2, ♂ 4.2–5.8

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3267 | 43 | 3224 | 4.42 | 3.81 | 5.05 | [3.79, 3.84] | [5.02, 5.07] |
| ♀ 40 60 | 1501 | 34 | 1467 | 4.36 | 3.78 | 4.98 | [3.76, 3.80] | [4.93, 5.01] |
| ♀ 60 80 | 293 | 5 | 288 | 4.38 | 3.83 | 5.05 | [3.68, 3.88] | [4.94, 5.14] |
| ♂ 20 40 | 2832 | 29 | 2803 | 5.04 | 4.36 | 5.78 | [4.33, 4.38] | [5.75, 5.81] |
| ♂ 40 60 | 1171 | 31 | 1140 | 4.90 | 4.22 | 5.60 | [4.18, 4.26] | [5.55, 5.65] |
| ♂ 60 80 | 334 | 8 | 326 | 4.77 | 3.98 | 5.47 | [3.94, 4.09] | [5.40, 5.51] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 71.67, z_crit = 15.03 → **partition justified**
- 40_60: z = 41.79, z_crit = 9.89 → **partition justified**
- 60_80: z = 13.94, z_crit = 4.80 → **partition justified**

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 5.60, z_crit = 13.26 → not justified
- female, 40-60 vs 60-80: z = 1.23, z_crit = 8.11 → not justified
- male, 20-40 vs 40-60: z = 11.40, z_crit = 12.16 → not justified
- male, 40-60 vs 60-80: z = 6.08, z_crit = 7.41 → not justified

---

### 2.13 Hemoglobin (g/dL) — code `hb_gdl`

*Textbook:* ♀ 12–16, ♂ 13–17.5

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3267 | 97 | 3170 | 13.40 | 11.42 | 15.10 | [11.40, 11.60] | [15.00, 15.10] |
| ♀ 40 60 | 1501 | 50 | 1451 | 13.40 | 11.30 | 15.20 | [11.20, 11.40] | [15.00, 15.30] |
| ♀ 60 80 | 293 | 4 | 289 | 13.60 | 12.00 | 15.48 | [11.80, 12.10] | [15.20, 15.80] |
| ♂ 20 40 | 2832 | 28 | 2804 | 15.40 | 13.50 | 17.20 | [13.40, 13.50] | [17.10, 17.30] |
| ♂ 40 60 | 1171 | 43 | 1128 | 15.10 | 13.30 | 16.90 | [13.20, 13.50] | [16.80, 17.00] |
| ♂ 60 80 | 334 | 8 | 326 | 14.95 | 12.81 | 16.70 | [12.50, 13.00] | [16.50, 16.80] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 81.89, z_crit = 14.97 → **partition justified**
- 40_60: z = 47.55, z_crit = 9.83 → **partition justified**
- 60_80: z = 16.14, z_crit = 4.80 → **partition justified**

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 0.48, z_crit = 13.16 → not justified
- female, 40-60 vs 60-80: z = 4.42, z_crit = 8.08 → not justified
- male, 20-40 vs 40-60: z = 7.27, z_crit = 12.14 → not justified
- male, 40-60 vs 60-80: z = 3.81, z_crit = 7.38 → not justified

---

### 2.14 Hematocrit (%) — code `hct`

*Textbook:* ♀ 35–47, ♂ 41–53

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3267 | 68 | 3199 | 39.30 | 34.00 | 44.50 | [33.90, 34.20] | [44.30, 44.70] |
| ♀ 40 60 | 1501 | 56 | 1445 | 39.30 | 33.70 | 44.50 | [33.41, 34.01] | [44.30, 44.70] |
| ♀ 60 80 | 293 | 4 | 289 | 40.20 | 35.04 | 45.36 | [34.64, 35.80] | [44.86, 46.34] |
| ♂ 20 40 | 2832 | 22 | 2810 | 45.10 | 39.70 | 50.70 | [39.50, 39.82] | [50.50, 50.90] |
| ♂ 40 60 | 1171 | 16 | 1155 | 44.30 | 38.30 | 49.90 | [37.88, 38.80] | [49.31, 50.30] |
| ♂ 60 80 | 334 | 8 | 326 | 43.95 | 38.00 | 49.79 | [37.16, 38.45] | [48.92, 50.58] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 82.67, z_crit = 15.01 → **partition justified**
- 40_60: z = 45.94, z_crit = 9.87 → **partition justified**
- 60_80: z = 16.75, z_crit = 4.80 → **partition justified**

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 0.25, z_crit = 13.20 → not justified
- female, 40-60 vs 60-80: z = 4.53, z_crit = 8.06 → not justified
- male, 20-40 vs 40-60: z = 8.19, z_crit = 12.19 → not justified
- male, 40-60 vs 60-80: z = 2.21, z_crit = 7.45 → not justified

---

### 2.15 MCV (fL) — code `mcv`

*Textbook:* ♀ 80–100, ♂ 80–100

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3267 | 136 | 3131 | 89.40 | 80.50 | 96.97 | [80.03, 80.90] | [96.80, 97.40] |
| ♀ 40 60 | 1501 | 81 | 1420 | 90.80 | 81.10 | 98.35 | [80.75, 81.69] | [98.05, 98.90] |
| ♀ 60 80 | 293 | 6 | 287 | 91.70 | 83.92 | 99.57 | [80.84, 84.50] | [98.97, 100.30] |
| ♂ 20 40 | 2832 | 85 | 2747 | 89.70 | 82.30 | 96.93 | [82.00, 82.56] | [96.60, 97.13] |
| ♂ 40 60 | 1171 | 41 | 1130 | 90.70 | 83.12 | 98.40 | [82.44, 83.80] | [98.08, 98.60] |
| ♂ 60 80 | 334 | 15 | 319 | 92.30 | 84.58 | 99.80 | [83.60, 85.50] | [98.80, 100.90] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 3.49, z_crit = 14.85 → not justified (collapse)
- 40_60: z = 1.31, z_crit = 9.78 → not justified (collapse)
- 60_80: z = 1.83, z_crit = 4.77 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 9.00, z_crit = 13.06 → not justified
- female, 40-60 vs 60-80: z = 3.95, z_crit = 8.00 → not justified
- male, 20-40 vs 40-60: z = 8.01, z_crit = 12.06 → not justified
- male, 40-60 vs 60-80: z = 5.96, z_crit = 7.37 → not justified

---

### 2.16 MCH (pg) — code `mch`

*Textbook:* ♀ 27–33, ♂ 27–33

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3267 | 146 | 3121 | 30.50 | 26.70 | 33.60 | [26.60, 26.80] | [33.40, 33.60] |
| ♀ 40 60 | 1501 | 94 | 1407 | 30.90 | 27.02 | 34.00 | [26.90, 27.30] | [33.80, 34.20] |
| ♀ 60 80 | 293 | 7 | 286 | 31.25 | 27.80 | 33.90 | [27.60, 28.10] | [33.60, 34.40] |
| ♂ 20 40 | 2832 | 82 | 2750 | 30.60 | 27.40 | 33.30 | [27.30, 27.50] | [33.30, 33.40] |
| ♂ 40 60 | 1171 | 48 | 1123 | 30.90 | 27.80 | 33.90 | [27.70, 28.00] | [33.70, 34.10] |
| ♂ 60 80 | 334 | 16 | 318 | 31.40 | 28.30 | 34.50 | [27.80, 28.79] | [33.90, 34.62] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 4.28, z_crit = 14.84 → not justified (collapse)
- 40_60: z = 2.55, z_crit = 9.74 → not justified (collapse)
- 60_80: z = 1.96, z_crit = 4.76 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 7.41, z_crit = 13.03 → not justified
- female, 40-60 vs 60-80: z = 2.74, z_crit = 7.97 → not justified
- male, 20-40 vs 40-60: z = 7.40, z_crit = 12.05 → not justified
- male, 40-60 vs 60-80: z = 4.03, z_crit = 7.35 → not justified

---

### 2.17 MCHC (g/dL) — code `mchc`

*Textbook:* ♀ 31.5–36.5, ♂ 31.5–36.5

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3267 | 55 | 3212 | 34.00 | 32.10 | 35.60 | [32.00, 32.20] | [35.50, 35.70] |
| ♀ 40 60 | 1501 | 41 | 1460 | 33.90 | 32.30 | 35.60 | [32.10, 32.30] | [35.50, 35.70] |
| ♀ 60 80 | 293 | 12 | 281 | 33.80 | 32.60 | 35.40 | [32.30, 32.70] | [35.00, 35.50] |
| ♂ 20 40 | 2833 | 63 | 2770 | 34.00 | 32.40 | 35.68 | [32.30, 32.50] | [35.60, 35.70] |
| ♂ 40 60 | 1171 | 21 | 1150 | 34.00 | 32.50 | 35.60 | [32.40, 32.50] | [35.40, 35.70] |
| ♂ 60 80 | 334 | 10 | 324 | 33.90 | 32.40 | 35.29 | [32.30, 32.51] | [35.10, 35.49] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 4.23, z_crit = 14.98 → not justified (collapse)
- 40_60: z = 3.41, z_crit = 9.89 → not justified (collapse)
- 60_80: z = 0.38, z_crit = 4.76 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 0.46, z_crit = 13.24 → not justified
- female, 40-60 vs 60-80: z = 1.14, z_crit = 8.08 → not justified
- male, 20-40 vs 40-60: z = 0.21, z_crit = 12.12 → not justified
- male, 40-60 vs 60-80: z = 3.04, z_crit = 7.43 → not justified

---

### 2.18 RDW (%) — code `rdw`

*Textbook:* ♀ 11.5–15, ♂ 11.5–15

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3265 | 166 | 3099 | 12.60 | 11.30 | 14.60 | [11.30, 11.40] | [14.50, 14.70] |
| ♀ 40 60 | 1497 | 107 | 1390 | 12.60 | 11.50 | 14.70 | [11.40, 11.50] | [14.53, 14.80] |
| ♀ 60 80 | 293 | 1 | 292 | 12.90 | 11.50 | 14.70 | [11.40, 11.60] | [14.47, 14.87] |
| ♂ 20 40 | 2832 | 38 | 2794 | 12.50 | 11.40 | 14.10 | [11.40, 11.50] | [14.00, 14.10] |
| ♂ 40 60 | 1171 | 32 | 1139 | 12.70 | 11.60 | 14.20 | [11.50, 11.60] | [14.10, 14.30] |
| ♂ 60 80 | 333 | 12 | 321 | 13.00 | 11.80 | 14.50 | [11.60, 11.90] | [14.40, 14.70] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 4.76, z_crit = 14.87 → not justified (collapse)
- 40_60: z = 1.03, z_crit = 9.74 → not justified (collapse)
- 60_80: z = 0.96, z_crit = 4.79 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 3.36, z_crit = 12.97 → not justified
- female, 40-60 vs 60-80: z = 3.75, z_crit = 7.94 → not justified
- male, 20-40 vs 40-60: z = 6.31, z_crit = 12.14 → not justified
- male, 40-60 vs 60-80: z = 6.46, z_crit = 7.40 → not justified

---

### 2.19 Platelets (×10⁹/L) — code `plt`

*Textbook:* ♀ 150–450, ♂ 150–450

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3266 | 62 | 3204 | 254.00 | 163.00 | 379.00 | [160.00, 165.00] | [376.00, 385.00] |
| ♀ 40 60 | 1501 | 30 | 1471 | 251.00 | 158.50 | 378.00 | [153.75, 166.04] | [372.00, 386.00] |
| ♀ 60 80 | 293 | 8 | 285 | 236.00 | 150.20 | 357.30 | [147.00, 160.00] | [338.79, 381.77] |
| ♂ 20 40 | 2832 | 57 | 2775 | 234.00 | 152.00 | 338.00 | [149.00, 155.00] | [332.65, 342.00] |
| ♂ 40 60 | 1171 | 20 | 1151 | 233.00 | 149.00 | 346.25 | [141.00, 153.26] | [341.00, 353.00] |
| ♂ 60 80 | 334 | 5 | 329 | 219.00 | 131.60 | 336.40 | [121.99, 153.20] | [309.80, 343.00] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 17.15, z_crit = 14.97 → **partition justified**
- 40_60: z = 9.47, z_crit = 9.92 → not justified (collapse)
- 60_80: z = 4.63, z_crit = 4.80 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 1.73, z_crit = 13.24 → not justified
- female, 40-60 vs 60-80: z = 4.17, z_crit = 8.11 → not justified
- male, 20-40 vs 40-60: z = 0.02, z_crit = 12.13 → not justified
- male, 40-60 vs 60-80: z = 4.38, z_crit = 7.45 → not justified

---

### 2.20 MPV (fL) — code `mpv`

*Textbook:* ♀ 7–11.5, ♂ 7–11.5

| Partition | n (raw) | outliers | n (final) | median | LRL (2.5%) | URL (97.5%) | LRL 90% CI | URL 90% CI |
|---|---:|---:|---:|---:|---:|---:|---|---|
| ♀ 20 40 | 3267 | 39 | 3228 | 8.10 | 6.70 | 10.03 | [6.70, 6.80] | [10.00, 10.20] |
| ♀ 40 60 | 1501 | 30 | 1471 | 8.10 | 6.70 | 9.80 | [6.60, 6.80] | [9.80, 9.90] |
| ♀ 60 80 | 293 | 4 | 289 | 8.10 | 6.60 | 10.10 | [6.40, 6.80] | [9.88, 10.20] |
| ♂ 20 40 | 2832 | 49 | 2783 | 8.10 | 6.70 | 9.90 | [6.70, 6.80] | [9.80, 10.00] |
| ♂ 40 60 | 1171 | 29 | 1142 | 8.00 | 6.60 | 9.60 | [6.60, 6.60] | [9.60, 9.70] |
| ♂ 60 80 | 334 | 5 | 329 | 8.00 | 6.42 | 9.70 | [6.30, 6.80] | [9.50, 9.88] |

*Harris-Boyd — sex partition within age bands:*
- 20_40: z = 3.69, z_crit = 15.01 → not justified (collapse)
- 40_60: z = 4.21, z_crit = 9.90 → not justified (collapse)
- 60_80: z = 2.09, z_crit = 4.81 → not justified (collapse)

*Harris-Boyd — age partition within each sex:*
- female, 20-40 vs 40-60: z = 3.44, z_crit = 13.27 → not justified
- female, 40-60 vs 60-80: z = 0.51, z_crit = 8.12 → not justified
- male, 20-40 vs 40-60: z = 5.14, z_crit = 12.13 → not justified
- male, 40-60 vs 60-80: z = 0.32, z_crit = 7.43 → not justified

---
