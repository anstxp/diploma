<template>
  <section class="section">
    <h2><i class="fa-solid fa-gear"></i> {{ $t('profile.settings.title') }}</h2>
    <div class="grid">
      <div class="field">
        <label>{{ $t('profile.settings.languageLabel') }}</label>
        <select :value="modelValue.preferredLanguage"
                @change="onLanguageChange($event.target.value)">
          <option value="uk">{{ $t('profile.settings.languageUk') }}</option>
          <option value="en">{{ $t('profile.settings.languageEn') }}</option>
        </select>
        <small class="hint-line">{{ $t('profile.settings.languageHelp') }}</small>
      </div>
      <div class="field">
        <label>{{ $t('profile.settings.unitsLabel') }}</label>
        <select :value="modelValue.unitsSystem"
                @change="update('unitsSystem', $event.target.value)">
          <option value="metric">{{ $t('profile.settings.unitsMetric') }}</option>
          <option value="imperial">{{ $t('profile.settings.unitsImperial') }}</option>
        </select>
      </div>
    </div>
  </section>
</template>

<script>
import { setLocale } from "@/i18n";

export default {
  name: "SettingsSection",
  props: { modelValue: { type: Object, required: true } },
  emits: ["update:modelValue"],
  methods: {
    update(field, value) {
      this.$emit("update:modelValue", { ...this.modelValue, [field]: value });
    },
    onLanguageChange(value) {
      this.update("preferredLanguage", value);
      setLocale(value);
    },
  },
};
</script>
