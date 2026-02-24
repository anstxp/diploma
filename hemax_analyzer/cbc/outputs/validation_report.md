# CBC Rules Engine — Validation Report on NHANES Master Dataset

## 1. Protocol

The CBC interpreter was executed on **119,555 participant records** from the harmonised NHANES 1999-2023 dataset. For each record, canonical master columns were mapped to the engine's payload schema (sex, age, full CBC with differential) and the resulting signal list, severity and flags were recorded. Two analytical strata were used: the **healthy reference cohort** (n=9,088, used to estimate the engine's specificity baseline) and the **full population** (used to characterise signal prevalence and to evaluate diagnostic performance against deterministic lab-based ground truth).

Ground-truth definitions for signals whose clinical meaning is entirely determined by lab values:

| Signal | Ground-truth definition |
|---|---|
| anemia_possible | Hb < 12 g/dL (♀) or Hb < 13 g/dL (♂) (WHO) |
| leukocytosis / leukopenia | WBC > 11 / < 4 × 10⁹/L |
| neutrophilia / neutropenia | ANC > 7.5 / < 1.5 × 10⁹/L |
| lymphocytosis / lymphopenia | ALC > 4 / < 1 × 10⁹/L |
| thrombocytosis / thrombocytopenia | PLT > 450 / < 150 × 10⁹/L |
| microcytic_anemia_pattern | Hb < cutoff ∧ MCV < 80 fL |
| macrocytic_anemia_pattern | Hb < cutoff ∧ MCV > 100 fL |
| normocytic_anemia_pattern | Hb < cutoff ∧ 80 ≤ MCV ≤ 100 fL |
| pancytopenia_pattern | WBC < 4 ∧ Hb < cutoff ∧ PLT < 150 |

## 2. Specificity on the healthy reference cohort

On the healthy cohort (n=9,088) the engine raised **at least one non-quality signal in 17.4% of records** — i.e. the no-signal rate was **82.6%**. The mean number of signals per healthy record was 0.25 (median 0).

*Per-signal false-positive rate on healthy cohort (top 15 most frequently fired):*

| Signal | False-positive rate |
|---|---:|
| `anemia_possible` | 3.8% |
| `monocytosis` | 3.6% |
| `normocytic_anemia_pattern` | 3.3% |
| `eosinophilia` | 2.6% |
| `thrombocytopenia` | 1.5% |
| `leukopenia` | 1.5% |
| `microcytosis_without_anemia` | 1.4% |
| `high_rdw` | 1.3% |
| `basophilia` | 1.2% |
| `leukocytosis` | 1.1% |
| `neutrophilia` | 0.8% |
| `microcytic_anemia_pattern` | 0.5% |
| `lymphocytosis` | 0.5% |
| `high_hgb` | 0.5% |
| `lymphopenia` | 0.4% |

## 3. Signal prevalence in the full population

On the full dataset (n=119,555) **at least one signal was raised in 29.6% of records**; mean 0.59, median 0, 95th percentile 3.

*All 23 signals, sorted by population prevalence:*

| Signal | n fired | Population rate | Healthy FPR |
|---|---:|---:|---:|
| `missing_core_cbc` | 24,413 | 20.4% | 0.2% |
| `anemia_possible` | 8,839 | 7.4% | 3.8% |
| `microcytosis_without_anemia` | 7,192 | 6.0% | 1.4% |
| `high_rdw` | 5,906 | 4.9% | 1.3% |
| `normocytic_anemia_pattern` | 5,451 | 4.6% | 3.3% |
| `monocytosis` | 5,384 | 4.5% | 3.6% |
| `leukopenia` | 4,176 | 3.5% | 1.5% |
| `neutrophilia` | 3,555 | 3.0% | 0.8% |
| `leukocytosis` | 3,541 | 3.0% | 1.1% |
| `microcytic_anemia_pattern` | 3,184 | 2.7% | 0.5% |
| `eosinophilia` | 2,567 | 2.1% | 2.6% |
| `thrombocytopenia` | 2,293 | 1.9% | 1.5% |
| `thrombocytosis` | 1,938 | 1.6% | 0.0% |
| `iron_deficiency_likely_pattern` | 1,844 | 1.5% | 0.1% |
| `lymphopenia` | 1,804 | 1.5% | 0.4% |
| `low_mchc_hypochromia` | 1,433 | 1.2% | 0.3% |
| `basophilia` | 1,284 | 1.1% | 1.2% |
| `neutropenia` | 1,253 | 1.0% | 0.0% |
| `high_hgb` | 1,123 | 0.9% | 0.5% |
| `lymphocytosis` | 1,001 | 0.8% | 0.5% |
| `nlr_high` | 995 | 0.8% | 0.0% |
| `macrocytosis_without_anemia` | 967 | 0.8% | 0.0% |
| `high_mchc_note` | 960 | 0.8% | 0.2% |
| `hemoconcentration_possible` | 737 | 0.6% | 0.1% |
| `plt_high_microcytosis_combo` | 732 | 0.6% | 0.0% |
| `bicytopenia_wbc_hgb` | 499 | 0.4% | 0.1% |
| `thal_trait_like_pattern` | 473 | 0.4% | 0.1% |
| `bicytopenia_hgb_plt` | 306 | 0.3% | 0.1% |
| `macrocytic_anemia_pattern` | 204 | 0.2% | 0.0% |
| `bicytopenia_wbc_plt` | 180 | 0.2% | 0.0% |
| `low_plt_high_mpv` | 71 | 0.1% | 0.0% |
| `pancytopenia_pattern` | 67 | 0.1% | 0.0% |
| `low_plt_low_mpv` | 48 | 0.0% | 0.0% |
| `relative_neutrophilia` | 0 | 0.0% | 0.0% |
| `relative_lymphocytosis` | 0 | 0.0% | 0.0% |

## 4. Diagnostic performance against deterministic ground truth

Sensitivity, specificity, precision and F1 are computed only on records whose ground-truth indicator was computable (i.e., the required lab values were present).

| Signal | n eval. | GT prev. | Eng. prev. | Sens | Spec | Prec | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `anemia_possible` | 62,692 | 10.1% | 10.1% | 100.0% | 100.0% | 100.0% | 1.000 |
| `high_hgb` | 62,692 | 1.1% | 1.1% | 100.0% | 100.0% | 100.0% | 1.000 |
| `high_rdw` | 62,692 | 7.5% | 7.5% | 100.0% | 100.0% | 100.0% | 1.000 |
| `microcytic_anemia_pattern` | 62,692 | 2.8% | 2.8% | 100.0% | 100.0% | 100.0% | 1.000 |
| `macrocytic_anemia_pattern` | 62,692 | 0.3% | 0.3% | 100.0% | 100.0% | 100.0% | 1.000 |
| `normocytic_anemia_pattern` | 62,692 | 6.9% | 6.9% | 100.0% | 100.0% | 100.0% | 1.000 |
| `leukocytosis` | 62,691 | 5.3% | 5.3% | 100.0% | 100.0% | 100.0% | 1.000 |
| `leukopenia` | 62,691 | 2.7% | 2.7% | 100.0% | 100.0% | 100.0% | 1.000 |
| `thrombocytosis` | 62,691 | 1.0% | 1.0% | 100.0% | 100.0% | 100.0% | 1.000 |
| `thrombocytopenia` | 62,691 | 3.4% | 3.4% | 100.0% | 100.0% | 100.0% | 1.000 |
| `pancytopenia_pattern` | 62,690 | 0.1% | 0.1% | 100.0% | 100.0% | 100.0% | 1.000 |
| `neutrophilia` | 62,523 | 4.8% | 4.8% | 100.0% | 100.0% | 100.0% | 1.000 |
| `neutropenia` | 62,523 | 1.1% | 1.1% | 100.0% | 100.0% | 100.0% | 1.000 |
| `lymphocytosis` | 62,523 | 1.4% | 1.4% | 100.0% | 100.0% | 100.0% | 1.000 |
| `lymphopenia` | 62,523 | 2.0% | 2.0% | 100.0% | 100.0% | 100.0% | 1.000 |
| `eosinophilia` | 62,523 | 3.2% | 3.2% | 100.0% | 100.0% | 100.0% | 1.000 |
| `monocytosis` | 62,523 | 7.0% | 7.0% | 100.0% | 100.0% | 100.0% | 1.000 |
| `basophilia` | 62,523 | 1.7% | 1.7% | 100.0% | 100.0% | 100.0% | 1.000 |

*Confusion matrix counts (for the record):*

| Signal | TP | FN | FP | TN |
|---|---:|---:|---:|---:|
| `anemia_possible` | 6,308 | 0 | 0 | 56,384 |
| `high_hgb` | 693 | 0 | 0 | 61,999 |
| `high_rdw` | 4,726 | 0 | 0 | 57,966 |
| `microcytic_anemia_pattern` | 1,772 | 0 | 0 | 60,920 |
| `macrocytic_anemia_pattern` | 201 | 0 | 0 | 62,491 |
| `normocytic_anemia_pattern` | 4,335 | 0 | 0 | 58,357 |
| `leukocytosis` | 3,326 | 0 | 0 | 59,365 |
| `leukopenia` | 1,682 | 0 | 0 | 61,009 |
| `thrombocytosis` | 632 | 0 | 0 | 62,059 |
| `thrombocytopenia` | 2,146 | 0 | 0 | 60,545 |
| `pancytopenia_pattern` | 65 | 0 | 0 | 62,625 |
| `neutrophilia` | 2,975 | 0 | 0 | 59,548 |
| `neutropenia` | 658 | 0 | 0 | 61,865 |
| `lymphocytosis` | 906 | 0 | 0 | 61,617 |
| `lymphopenia` | 1,226 | 0 | 0 | 61,297 |
| `eosinophilia` | 1,992 | 0 | 0 | 60,531 |
| `monocytosis` | 4,373 | 0 | 0 | 58,150 |
| `basophilia` | 1,039 | 0 | 0 | 61,484 |

## 5. Signal enrichment in self-reported disease

For each (self-reported label × engine signal) pair, we compared the signal rate in label-positive participants against label-negative participants. A lift >1 indicates the engine signal is more common in those with the self-reported diagnosis, serving as a sanity check of the engine's clinical coupling.

| Self-report | Signal | n (pos / neg) | Rate (pos / neg) | Lift |
|---|---|---:|---:|---:|
| `told_mi` | `anemia_possible` | 2,959 / 63,470 | 15.6% / 8.7% | 1.803 |
| `told_weak_kidney` | `anemia_possible` | 2,092 / 59,459 | 23.9% / 8.6% | 2.776 |
| `told_cancer` | `anemia_possible` | 6,753 / 59,729 | 11.2% / 8.7% | 1.285 |
| `told_diabetes` | `anemia_possible` | 8,440 / 104,544 | 16.7% / 7.0% | 2.407 |
| `told_diabetes` | `leukocytosis` | 8,440 / 104,544 | 6.1% / 2.8% | 2.142 |
| `told_htn` | `leukocytosis` | 23,863 / 51,875 | 4.9% / 4.2% | 1.173 |

## 6. Inter-cycle stability

To check that the engine behaves consistently across NHANES cycles (despite small methodological changes between survey cycles), we report the rate of key signals per cycle.

| Cycle | n | Any-signal rate | Anemia rate | Leukocytosis rate |
|---|---:|---:|---:|---:|
| 1999-2000 | 9,965 | 25.8% | 6.1% | 3.1% |
| 2001-2002 | 11,039 | 27.6% | 6.7% | 2.7% |
| 2003-2004 | 10,122 | 29.1% | 6.1% | 3.2% |
| 2005-2006 | 10,348 | 30.2% | 6.6% | 3.0% |
| 2007-2008 | 10,149 | 31.2% | 6.8% | 3.1% |
| 2009-2010 | 10,537 | 30.2% | 7.1% | 3.0% |
| 2011-2012 | 9,756 | 31.9% | 9.4% | 2.3% |
| 2013-2014 | 10,175 | 32.8% | 8.5% | 3.7% |
| 2015-2016 | 9,971 | 32.6% | 8.5% | 3.5% |
| 2017-2020 | 15,560 | 31.1% | 8.3% | 3.0% |
| 2021-2023 | 11,933 | 23.1% | 7.0% | 2.0% |

## 7. Summary of findings

*(Thesis-friendly framing — revise wording as needed.)*

- **Specificity on the healthy cohort** is 82.6% for the *no-signal* class. A well-calibrated clinical screener targeting a healthy adult population should raise no signals on ≥ 90% of such subjects; deviations below that threshold warrant re-examination of the responsible rules.
- Inter-cycle rates of anaemia and leukocytosis are stable, indicating no major cycle-specific artefact in the harmonised master.

These results form the baseline against which the next iteration of the engine — using empirically-derived reference intervals (§2.3) — is to be compared.
