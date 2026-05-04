import { t, getLocale } from "@/i18n";


export function normalizeKindCode(type) {
  const s = String(type ?? "").toLowerCase();
  if (s === "cbc"   || type === 1) return "cbc";
  if (s === "chem"  || type === 2) return "chem";
  if (s === "risk"  || type === 3) return "risk";
  if (s === "neuro" || type === 4) return "neuro";
  if (s === "derma" || type === 5) return "derma";
  return s;
}

export function kindLabel(type) {
  const code = normalizeKindCode(type);
  if (!code) return type || "—";
  return t(`analysis.kinds.${code}`);
}

export const KIND_LABELS = new Proxy(
  {},
  { get: (_t, key) => kindLabel(key) }
);


export const CBC_ANALYTES = {
  wbc:       { unit: "×10⁹/L",  range: "4.0 – 9.0",   low: 4.0,  high: 9.0 },
  rbc:       { unit: "×10¹²/L", range: "3.8 – 5.2",   low: 3.8,  high: 5.2 },
  hgb:       { unit: "g/dL",    range: "12.0 – 16.0", low: 12.0, high: 16.0 },
  hct:       { unit: "%",       range: "36 – 46",     low: 36,   high: 46 },
  mcv:       { unit: "fL",      range: "80 – 100",    low: 80,   high: 100 },
  mch:       { unit: "pg",      range: "27 – 33",     low: 27,   high: 33 },
  mchc:      { unit: "g/dL",    range: "32 – 36",     low: 32,   high: 36 },
  rdw:       { unit: "%",       range: "11.5 – 14.5", low: 11.5, high: 14.5 },
  plt:       { unit: "×10⁹/L",  range: "150 – 400",   low: 150,  high: 400 },
  mpv:       { unit: "fL",      range: "7.0 – 11.0",  low: 7.0,  high: 11.0 },
  neut_pct:  { unit: "%",       range: "47 – 72",     low: 47,   high: 72 },
  lymph_pct: { unit: "%",       range: "19 – 37",     low: 19,   high: 37 },
  mono_pct:  { unit: "%",       range: "3 – 11",      low: 3,    high: 11 },
  eos_pct:   { unit: "%",       range: "0.5 – 5.0",   low: 0.5,  high: 5.0 },
  baso_pct:  { unit: "%",       range: "0 – 1.0",     low: 0,    high: 1.0 },
  esr:       { unit: "мм/год",  range: "0 – 20",      low: null, high: 20 },
};

/** Same for CHEM. */
export const CHEM_ANALYTES = {
  glucose:           { unit: "ммоль/л",  range: "3.9 – 6.1",   low: 3.9,  high: 6.1 },
  urea:              { unit: "ммоль/л",  range: "2.5 – 8.3",   low: 2.5,  high: 8.3 },
  creatinine:        { unit: "мкмоль/л", range: "62 – 106",    low: 62,   high: 106 },
  alt:               { unit: "U/L",      range: "0 – 41",      low: 0,    high: 41 },
  ast:               { unit: "U/L",      range: "0 – 40",      low: 0,    high: 40 },
  bilirubin_total:   { unit: "мкмоль/л", range: "5 – 21",      low: 5,    high: 21 },
  bilirubin_direct:  { unit: "мкмоль/л", range: "0 – 5.1",     low: 0,    high: 5.1 },
  cholesterol_total: { unit: "ммоль/л",  range: "< 5.2",       low: null, high: 5.2 },
  hdl:               { unit: "ммоль/л",  range: "> 1.0",       low: 1.0,  high: null },
  ldl:               { unit: "ммоль/л",  range: "< 3.0",       low: null, high: 3.0 },
  triglycerides:     { unit: "ммоль/л",  range: "< 1.7",       low: null, high: 1.7 },
  protein_total:     { unit: "г/л",      range: "65 – 85",     low: 65,   high: 85 },
  albumin:           { unit: "г/л",      range: "35 – 52",     low: 35,   high: 52 },
  potassium:         { unit: "ммоль/л",  range: "3.5 – 5.1",   low: 3.5,  high: 5.1 },
  sodium:            { unit: "ммоль/л",  range: "136 – 145",   low: 136,  high: 145 },
};

const UNIT_DISPLAY_EN = {
  // SI concentration
  "ммоль/л":   "mmol/L",
  "мкмоль/л":  "μmol/L",
  "г/л":       "g/L",
  "мг/л":      "mg/L",
  "нг/мл":     "ng/mL",
  // Time / rate
  "мм/год":    "mm/h",
  "уд/хв":     "bpm",
  // Length / mass
  "см":        "cm",
  "кг":        "kg",
  // Blood pressure
  "мм рт.ст.": "mmHg",
};

export function displayUnit(unit) {
  if (!unit) return "";
  return getLocale() === "en" ? (UNIT_DISPLAY_EN[unit] || unit) : unit;
}

export function cbcLabel(code) {
  return t(`results.analyteLabels.cbc.${code}`);
}

/** Localized CHEM analyte label. */
export function chemLabel(code) {
  return t(`results.analyteLabels.chem.${code}`);
}


export function dermaClassName(code) {
  return t(`results.dermaClass.${code}`);
}

export const DERMA_CLASS_NAMES_UA = new Proxy(
  {},
  { get: (_t, key) => dermaClassName(key) }
);


const TONE_VISUAL = {
  normal:           { class: "ok",    icon: "fa-check-circle" },
  attention_needed: { class: "warn",  icon: "fa-circle-exclamation" },
  urgent:           { class: "alert", icon: "fa-triangle-exclamation" },
  incomplete:       { class: "info",  icon: "fa-circle-info" },
  neutral:          { class: "info",  icon: "fa-circle-info" },
};

export function toneConfig(tone) {
  const v = TONE_VISUAL[tone] || TONE_VISUAL.normal;
  return { ...v, title: t(`tone.${tone || "normal"}`) };
}

export const TONE_CONFIG = new Proxy(
  {},
  { get: (_t, key) => toneConfig(key) }
);


export function tierLabel(tier) {
  return t(`tier.${tier}`);
}

export const tierLabelUa = tierLabel;


const DIRECTION_VISUAL = {
  raises:  { icon: "fa-arrow-trend-up",   class: "drives-up" },
  lowers:  { icon: "fa-arrow-trend-down", class: "drives-down" },
  neutral: { icon: "fa-minus",            class: "drives-flat" },
};

export function directionConfig(dir) {
  const v = DIRECTION_VISUAL[dir] || DIRECTION_VISUAL.neutral;
  return { ...v, label: t(`results.topDrivers.${dir || "neutral"}`) };
}

// Back-compat proxy
export const DIRECTION_CONFIG = new Proxy(
  {},
  { get: (_t, key) => directionConfig(key) }
);


export function featureLabel(key) {
  const path = `results.features.${key}`;
  const v = t(path);
  return v === path ? key : v;
}

export const featureLabelUa = featureLabel;
