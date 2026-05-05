<template>
  <section class="section">
    <h2><i class="fa-solid fa-person-running"></i> {{ $t('profile.lifestyle.title') }}</h2>
    <div class="grid">
      <div class="field">
        <label class="checkbox">
          <input :checked="modelValue.smoker"
                 @change="update('smoker', $event.target.checked)"
                 type="checkbox" />
          <span>{{ $t('profile.lifestyle.smokerLabel') }}</span>
        </label>
      </div>
      <div class="field">
        <label>{{ $t('profile.lifestyle.alcoholLabel') }}</label>
        <select :value="modelValue.alcoholFrequency || 'Unknown'"
                @change="update('alcoholFrequency', $event.target.value)">
          <option value="Unknown">{{ $t('profile.lifestyle.alcoholUnknown') }}</option>
          <option value="Never">{{ $t('profile.lifestyle.alcoholNever') }}</option>
          <option value="Occasional">{{ $t('profile.lifestyle.alcoholOccasional') }}</option>
          <option value="Regular">{{ $t('profile.lifestyle.alcoholRegular') }}</option>
          <option value="Heavy">{{ $t('profile.lifestyle.alcoholHeavy') }}</option>
        </select>
      </div>
      <div class="field">
        <label>{{ $t('profile.lifestyle.activityLabel') }}</label>
        <select :value="modelValue.physicalActivity || 'Unknown'"
                @change="update('physicalActivity', $event.target.value)">
          <option value="Unknown">{{ $t('profile.lifestyle.activityUnknown') }}</option>
          <option value="Sedentary">{{ $t('profile.lifestyle.activitySedentary') }}</option>
          <option value="Light">{{ $t('profile.lifestyle.activityLight') }}</option>
          <option value="Moderate">{{ $t('profile.lifestyle.activityModerate') }}</option>
          <option value="Active">{{ $t('profile.lifestyle.activityActive') }}</option>
        </select>
      </div>
      <div class="field">
        <label>{{ $t('profile.lifestyle.dietLabel') }}</label>
        <select :value="modelValue.dietType || 'Unknown'"
                @change="update('dietType', $event.target.value)">
          <option value="Unknown">{{ $t('profile.lifestyle.dietUnknown') }}</option>
          <option value="Omnivore">{{ $t('profile.lifestyle.dietOmnivore') }}</option>
          <option value="Vegetarian">{{ $t('profile.lifestyle.dietVegetarian') }}</option>
          <option value="Vegan">{{ $t('profile.lifestyle.dietVegan') }}</option>
          <option value="Keto">{{ $t('profile.lifestyle.dietKeto') }}</option>
          <option value="Other">{{ $t('profile.lifestyle.dietOther') }}</option>
        </select>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: "LifestyleSection",
  props: { modelValue: { type: Object, required: true } },
  emits: ["update:modelValue"],
  methods: {
    update(field, value) {
      this.$emit("update:modelValue", { ...this.modelValue, [field]: value });
    },
  },
};
</script>
