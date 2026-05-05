<template>
  <span :class="['badge', badgeClass]">{{ label }}</span>
</template>

<script>
import { t } from "@/i18n";


const KEY_BY_NAME = {
  unknown:  "unknown",
  low:      "normal",
  normal:   "normal",
  mild:     "mild",
  watch:    "watch",
  moderate: "moderate",
  monitor:  "monitor",
  warning:  "warning",
  high:     "high",
  severe:   "severe",
  urgent:   "urgent",
  critical: "critical",
  "0":      "unknown",
  "1":      "normal",
  "2":      "mild",
  "3":      "monitor",
  "4":      "high",
};

const NORMAL_SET  = new Set(["normal", "low", "1"]);
const MONITOR_SET = new Set(["mild", "watch", "moderate", "monitor", "warning", "2", "3"]);
const URGENT_SET  = new Set(["high", "severe", "urgent", "critical", "4"]);

export default {
  name: "SeverityBadge",
  props: {
    severity: { type: [String, Number], default: "Unknown" },
  },
  computed: {
    label() {
      const s = String(this.severity || "").toLowerCase();
      const key = KEY_BY_NAME[s];
      if (key) return t(`severity.${key}`);
      // Unknown severity — show the raw value as a last resort.
      // Preserves forward-compat if backend introduces a new tier we
      // haven't translated yet (visible to the user as "Critical-2" or
      // whatever, rather than the dotted i18n path).
      return this.severity || t("severity.fallback");
    },
    badgeClass() {
      const s = String(this.severity || "").toLowerCase();
      if (NORMAL_SET.has(s))  return "badge-normal";
      if (MONITOR_SET.has(s)) return "badge-monitor";
      if (URGENT_SET.has(s))  return "badge-urgent";
      return "badge-info";
    },
  },
};
</script>
