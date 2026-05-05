<template>
  <div class="metric-row">
    <label :for="id">{{ label }} <span v-if="displayedUnit" class="unit">{{ displayedUnit }}</span></label>
    <input
      :id="id"
      :type="type"
      :step="step"
      :min="min"
      :max="max"
      class="box"
      :value="modelValue"
      @input="$emit('update:modelValue', cast($event.target.value))"
      :placeholder="placeholder"
    />
    <div v-if="hint" class="hint">{{ hint }}</div>
  </div>
</template>

<script>
import { displayUnit } from "@/constants/analysisConstants";

export default {
  name: "MetricInput",
  props: {
    id: { type: String, required: true },
    label: { type: String, required: true },
    unit: { type: String, default: "" },
    modelValue: { type: [String, Number], default: "" },
    type: { type: String, default: "number" },
    step: { type: [String, Number], default: "any" },
    min: { type: [String, Number], default: null },
    max: { type: [String, Number], default: null },
    placeholder: { type: String, default: "" },
    hint: { type: String, default: "" },
  },
  emits: ["update:modelValue"],
  computed: {
    displayedUnit() {
      return displayUnit(this.unit);
    },
  },
  methods: {
    cast(v) {
      if (this.type === "number") {
        if (v === "") return null;
        const n = Number(v);
        return isNaN(n) ? v : n;
      }
      return v;
    },
  },
};
</script>

<style scoped lang="scss">
.metric-row {
  display: grid;
  grid-template-columns: 1fr 14rem;
  gap: 1rem;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid rgba(0,0,0,0.05);

  label {
    font-size: 1.4rem;
    color: var(--black);
    text-transform: none;
  }

  .unit {
    color: var(--light-color);
    font-size: 1.2rem;
    margin-left: 0.4rem;
  }

  .box {
    width: 100%;
    padding: 0.7rem 1rem;
    font-size: 1.4rem;
    border: var(--border);
    border-radius: 0.4rem;
    text-align: right;

    &:focus { border-color: var(--purple); }
  }

  .hint {
    grid-column: 1 / -1;
    font-size: 1.1rem;
    color: var(--light-color);
    text-transform: none;
  }
}

@media (max-width: 600px) {
  .metric-row {
    grid-template-columns: 1fr;
    gap: 0.4rem;

    .box { text-align: left; }
  }
}
</style>
