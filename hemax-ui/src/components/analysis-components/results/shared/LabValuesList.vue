<template>
  <div v-if="values.length" class="lab-values">
    <h4>{{ $t('results.headers.labValues') }}</h4>
    <div class="values-grid">
      <div v-for="v in values" :key="v.code" :class="['value-row', v.flag]">
        <span class="v-label">{{ v.label }}</span>
        <span class="v-value">
          <span class="v-num">{{ v.formattedValue }}</span>
          <small class="v-unit">{{ v.unit }}</small>
          <i v-if="v.flag === 'high'" class="fa-solid fa-arrow-up high"></i>
          <i v-else-if="v.flag === 'low'" class="fa-solid fa-arrow-down low"></i>
        </span>
        <span v-if="v.range" class="v-range">{{ v.range }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import {
  CBC_ANALYTES, CHEM_ANALYTES,
  cbcLabel, chemLabel,
  displayUnit,
} from "@/constants/analysisConstants";

export default {
  name: "LabValuesList",
  props: {
    kind:      { type: String, required: true },
    rawValues: { type: Object, default: () => ({}) },
  },
  computed: {
    dictionary() {
      if (this.kind === "cbc")  return CBC_ANALYTES;
      if (this.kind === "chem") return CHEM_ANALYTES;
      return null;
    },
    labelFor() {
      if (this.kind === "cbc")  return cbcLabel;
      if (this.kind === "chem") return chemLabel;
      return (code) => code;
    },
    values() {
      if (!this.dictionary || !this.rawValues) return [];
      const rows = [];
      for (const [code, def] of Object.entries(this.dictionary)) {
        const raw = this.rawValues[code];
        if (raw == null) continue;
        const num = typeof raw === "number" ? raw : parseFloat(raw);
        if (Number.isNaN(num)) continue;

        let flag = "ok";
        if (def.low != null && num < def.low) flag = "low";
        else if (def.high != null && num > def.high) flag = "high";

        rows.push({
          code,
          label: this.labelFor(code),
          unit: displayUnit(def.unit),
          range: def.range,
          formattedValue: Number.isInteger(num) ? num : num.toFixed(2),
          flag,
        });
      }
      return rows;
    },
  },
};
</script>
