<template>
  <section class="section">
    <h2><i class="fa-solid fa-phone"></i> {{ $t('profile.emergency.title') }}</h2>
    <div class="grid">
      <div class="field">
        <label>{{ $t('profile.emergency.nameLabel') }}</label>
        <input :value="modelValue.emergencyContactName"
               @input="update('emergencyContactName', $event.target.value)"
               type="text" maxlength="160" />
      </div>
      <div class="field">
        <label>{{ $t('profile.emergency.phoneLabel') }}</label>
        <input :value="modelValue.emergencyContactPhone"
               @input="update('emergencyContactPhone', $event.target.value)"
               type="tel" maxlength="40" />
      </div>
      <div class="field">
        <label>{{ $t('profile.emergency.relationLabel') }}</label>
        <input :value="modelValue.emergencyContactRelation"
               @input="update('emergencyContactRelation', $event.target.value)"
               type="text" maxlength="80"
               :placeholder="$t('profile.emergency.relationPlaceholder')" />
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: "EmergencyContactSection",
  props: { modelValue: { type: Object, required: true } },
  emits: ["update:modelValue"],
  methods: {
    update(field, value) {
      this.$emit("update:modelValue", { ...this.modelValue, [field]: value });
    },
  },
};
</script>
