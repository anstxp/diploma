<template>
  <section class="section">
    <h2><i class="fa-solid fa-heart-pulse"></i> {{ $t('profile.vitals.title') }}</h2>
    <p class="section-hint">{{ $t('profile.vitals.hint') }}</p>
    <div class="grid">
      <div class="field">
        <label>{{ $t('profile.vitals.sbpLabel') }}</label>
        <input :value="modelValue.typicalSystolicBp"
               @input="updateNum('typicalSystolicBp', $event.target.value)"
               type="number" min="60" max="250" />
      </div>
      <div class="field">
        <label>{{ $t('profile.vitals.dbpLabel') }}</label>
        <input :value="modelValue.typicalDiastolicBp"
               @input="updateNum('typicalDiastolicBp', $event.target.value)"
               type="number" min="40" max="200" />
      </div>
      <div class="field">
        <label>{{ $t('profile.vitals.pulseLabel') }}</label>
        <input :value="modelValue.typicalRestingPulse"
               @input="updateNum('typicalRestingPulse', $event.target.value)"
               type="number" min="30" max="200" />
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: "VitalsSection",
  props: { modelValue: { type: Object, required: true } },
  emits: ["update:modelValue"],
  methods: {
    updateNum(field, raw) {
      const v = raw === "" ? null : Number(raw);
      this.$emit("update:modelValue", { ...this.modelValue, [field]: v });
    },
  },
};
</script>
