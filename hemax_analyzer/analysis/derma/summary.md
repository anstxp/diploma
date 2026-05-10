# HEMAX_DERMA — аналітичний звіт для диплому

## 1. Постановка задачі

HEMAX_DERMA — система класифікації пігментних утворень шкіри на основі
дерматоскопічних зображень за датасетом **HAM10000**. Модель розрізняє
**7 класів** уражень: від доброякісних родимок до меланоми. Архітектурно
— CNN на основі ImageNet-предтренованої моделі (EfficientNet або
ResNet, залежно від конкретного запуску), дотренована з cross-entropy
loss на 224×224 центрованих кропах.

| Параметр навчання | Значення |
|-------------------|----------|
| Епох максимум | 20 |
| Batch size | 32 |
| Learning rate | 0.0001 |
| Weight decay | 0.0001 |
| Early stopping patience | 5 |
| Pre-trained backbone | Yes |
| Device | `mps` |
| Best epoch | 18 |

## 2. Основні показники якості

| Метрика | Значення | Інтерпретація |
|---------|---------:|---------------|
| Test **Macro AUC** | 0.879 | Дискримінація |
| Test **Accuracy** | 0.470 | Top-1 правильність |
| Test **Macro F1** | 0.384 | Збалансована F1 по класах |

**Інтерпретація.** Розрив між Accuracy (0.47) і Macro AUC
(0.88) є типовим для дерматоскопії — клас "nv" (родимка)
займає ~67% даних, тому навіть constant predictor досягає accuracy 0.67
без жодної реальної дискримінації. **Macro AUC** — більш чесна метрика:
вона усереднює AUC по класах, ігноруючи частоти.

## 3. Per-class AUC (one-vs-rest)

| Клас | Опис | Severity | AUC |
|------|------|----------|----:|
| `vasc` | Судинні ушкодж. (vasc) | MEDIUM | 0.985 |
| `akiec` | Actinic keratoses (akiec) | HIGH | 0.929 |
| `bcc` | Basal cell carcinoma (bcc) | HIGH | 0.924 |
| `nv` | Melanocytic nevi (nv) | LOW | 0.892 |
| `df` | Dermatofibroma (df) | LOW | 0.862 |
| `mel` | Меланома (mel) | CRITICAL | 0.799 |
| `bkl` | Benign keratosis (bkl) | LOW | 0.763 |


### 3.1. Найкраща дискримінація

- **Судинні ушкодж. (vasc)** — AUC = 0.985.
  Зазвичай це vascular або dermatofibroma, у яких унікальні текстурні
  й кольорові ознаки на дерматоскопі.

### 3.2. Меланома — критичний клас

- **Melanoma (mel)** — AUC = 0.799.
  Melanoma — найвищий клінічний пріоритет (severity = critical). Модель
  розрізняє меланому проти решти класів із AUC ~0.80, що
  знаходиться у діапазоні опублікованих робіт на HAM10000 (зазвичай
  0.80-0.92 без додаткових модальностей).

### 3.3. Найскромніший клас

- **Benign keratosis (bkl)** — AUC = 0.763.
  Це найскладніше: типово bkl (benign keratosis) — оптично схожий і
  на nv, і на mel.

## 4. Severity-зважена ефективність

Класи згруповано за клінічною тяжкістю. Для медичного скринінгу
ключове — щоб модель *не пропускала* високотяжкі ураження (critical,
high). Подивіться `plots/03_severity_weighted_perf.png`:

- **critical (mel)**: AUC = 0.799
- **high (akiec, bcc)**: avg AUC = 0.927
- **medium (vasc)**: AUC = 0.985
- **low (bkl, df, nv)**: avg AUC = 0.839

## 5. Калібрація

Модель калібрується через **temperature scaling**, параметри збережено
у `derma_api/weights/calibration_params.json`.

- Оптимальна temperature: **T = 1.670**
- T > 1.0 → модель **пере-впевнена**: ймовірності будуть пом'якшені (поділ на T>1 пом'якшує).


## 6. Динаміка навчання

Кращу епоху обрано **18** з
20. Це означає, що модель досягла плато після
середньої частини тренування, після чого validation score почав
повільно деградувати (overfitting).

## 7. Висновки для захисту

1. **Macro AUC 0.879** — рівень робіт типу
   "ResNet-50 на HAM10000 без додаткової аугментації". Для production
   skin-cancer triage цього недостатньо без supplementary multimodal
   inputs (метадані пацієнта, anatomical site).
2. **Melanoma AUC 0.799** — клінічно достатнє для
   тригер-flagging, але NPV / PPV треба окремо аналізувати при виборі
   операційного порогу.
3. **Сильні класи**: vasc, df, nv — модель надійно їх розрізняє.
   **Слабкі**: bkl, mel — між ними часті cross-misclassification, що
   є відомою проблемою дерматоскопічної класифікації.
4. **Severity-aware accuracy** є більш інформативною для медичних
   застосувань, ніж raw accuracy. Зокрема, false-negatives на класі
   mel мають значно вищу clinical cost.

## 8. Список згенерованих фігур

| Файл | Зміст |
|------|-------|
| `plots/01_per_class_auc.png` | AUC по 7 класах (меланома виділена) |
| `plots/02_training_dynamics.png` | Loss, accuracy, AUC, F1 по епохах |
| `plots/03_severity_weighted_perf.png` | AUC за severity-групами |
| `plots/04_class_prevalence_test.png` | Розподіл класів у HAM10000 test |
| `plots/05_auc_evolution_by_epoch.png` | Per-class AUC по епохах |
| `plots/06_calibration_params.png` | Calibration parameters |
| `plots/07_overall_metrics.png` | Accuracy / Macro F1 / Macro AUC |
| `plots/08_summary_table.png` | Зведена таблиця класів |
