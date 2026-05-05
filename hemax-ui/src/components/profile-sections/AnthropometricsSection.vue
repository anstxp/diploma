<template>
  <section class="section">
    <h2><i class="fa-solid fa-ruler"></i> {{ $t('profile.anthro.title') }}</h2>
    <div class="grid">
      <div class="field">
        <label>{{ $t('profile.anthro.heightLabel') }}</label>
        <input :value="modelValue.heightCm" @input="updateNum('heightCm', $event.target.value)"
               type="number" min="50" max="250" step="0.5" />
      </div>
      <div class="field">
        <label>{{ $t('profile.anthro.weightLabel') }}</label>
        <input :value="modelValue.weightKg" @input="updateNum('weightKg', $event.target.value)"
               type="number" min="20" max="300" step="0.1" />
      </div>
      <div class="field">
        <label>{{ $t('profile.anthro.waistLabel') }}</label>
        <input :value="modelValue.waistCm" @input="updateNum('waistCm', $event.target.value)"
               type="number" min="40" max="250" />
      </div>
      <div class="field bmi-display">
        <label>{{ $t('profile.anthro.bmiLabel') }}</label>
        <div class="bmi-value">
          <strong v-if="computedBmi">{{ computedBmi }}</strong>
          <span v-else class="muted">—</span>
          <small v-if="computedBmi" :class="bmiClass(computedBmi)">{{ bmiCategory(computedBmi) }}</small>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
/** Height/weight/waist + computed BMI. */
export default {
  name: "AnthropometricsSection",
  props: { modelValue: { type: Object, required: true } },
  emits: ["update:modelValue"],
  computed: {
    computedBmi() {
      const h = this.modelValue.heightCm;
      const w = this.modelValue.weightKg;
      if (!h || !w) return null;
      const bmi = w / Math.pow(h / 100, 2);
      return bmi.toFixed(1);
    },
  },
  methods: {
    updateNum(field, raw) {
      const v = raw === "" ? null : Number(raw);
      this.$emit("update:modelValue", { ...this.modelValue, [field]: v });
    },
    bmiCategory(bmi) {
      const n = Number(bmi);
      if (n < 18.5) return this.$t('profile.anthro.bmiUnderweight');
      if (n < 25)   return this.$t('profile.anthro.bmiNormal');
      if (n < 30)   return this.$t('profile.anthro.bmiOverweight');
      return this.$t('profile.anthro.bmiObese');
    },
    bmiClass(bmi) {
      const n = Number(bmi);
      if (n < 18.5 || n >= 30) return "warn";
      if (n < 25) return "ok";
      return "neutral";
    },
  },
};
</script>
