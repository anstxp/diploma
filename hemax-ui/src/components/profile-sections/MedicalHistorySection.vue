<template>
  <section class="section">
    <h2>
      <i class="fa-solid fa-notes-medical"></i> {{ $t('profile.medicalHistory.title') }}
      <small class="encrypted-badge"><i class="fa-solid fa-lock"></i> {{ $t('profile.medicalHistory.encryptedBadge') }}</small>
    </h2>
    <p class="section-hint">{{ $t('profile.medicalHistory.hint') }}</p>
    <div class="field full">
      <label>{{ $t('profile.medicalHistory.chronicLabel') }}</label>
      <textarea :value="modelValue.chronicDiseases"
                @input="update('chronicDiseases', $event.target.value)"
                rows="3" maxlength="4000"
                :placeholder="$t('profile.medicalHistory.chronicPlaceholder')"></textarea>
    </div>
    <div class="field full">
      <label>{{ $t('profile.medicalHistory.allergiesLabel') }}</label>
      <textarea :value="modelValue.allergies"
                @input="update('allergies', $event.target.value)"
                rows="3" maxlength="4000"
                :placeholder="$t('profile.medicalHistory.allergiesPlaceholder')"></textarea>
    </div>
    <div class="field full">
      <label>{{ $t('profile.medicalHistory.medicationsLabel') }}</label>
      <textarea :value="modelValue.currentMedications"
                @input="update('currentMedications', $event.target.value)"
                rows="3" maxlength="4000"
                :placeholder="$t('profile.medicalHistory.medicationsPlaceholder')"></textarea>
    </div>
    <div class="field full">
      <label>{{ $t('profile.medicalHistory.familyLabel') }}</label>
      <textarea :value="modelValue.familyHistory"
                @input="update('familyHistory', $event.target.value)"
                rows="3" maxlength="4000"
                :placeholder="$t('profile.medicalHistory.familyPlaceholder')"></textarea>
    </div>
  </section>
</template>

<script>
export default {
  name: "MedicalHistorySection",
  props: { modelValue: { type: Object, required: true } },
  emits: ["update:modelValue"],
  methods: {
    update(field, value) {
      this.$emit("update:modelValue", { ...this.modelValue, [field]: value });
    },
  },
};
</script>
