<template>
  <section class="section">
    <h2><i class="fa-solid fa-user"></i> {{ $t('profile.personal.title') }}</h2>
    <div class="grid">
      <div class="field">
        <label>{{ $t('profile.personal.firstName') }}</label>
        <input :value="modelValue.firstName" @input="update('firstName', $event.target.value)"
               type="text" maxlength="80" />
      </div>
      <div class="field">
        <label>{{ $t('profile.personal.lastName') }}</label>
        <input :value="modelValue.lastName" @input="update('lastName', $event.target.value)"
               type="text" maxlength="80" />
      </div>
      <div class="field">
        <label>{{ $t('profile.personal.middleName') }}</label>
        <input :value="modelValue.middleName" @input="update('middleName', $event.target.value)"
               type="text" maxlength="80" />
      </div>
      <div class="field">
        <label>{{ $t('profile.personal.dateOfBirth') }}</label>
        <input :value="modelValue.dateOfBirth" @input="update('dateOfBirth', $event.target.value)"
               type="date" />
        <small v-if="computedAge != null" class="hint-line">
          {{ $t('profile.personal.ageHint') }} <strong>{{ computedAge }}</strong> {{ ageWord(computedAge) }}
        </small>
      </div>
      <div class="field">
        <label>{{ $t('profile.personal.sex') }}</label>
        <select :value="modelValue.sex || 'Unknown'"
                @change="update('sex', $event.target.value)">
          <option value="Unknown">{{ $t('profile.personal.sexUnknown') }}</option>
          <option value="Male">{{ $t('profile.personal.sexMale') }}</option>
          <option value="Female">{{ $t('profile.personal.sexFemale') }}</option>
        </select>
      </div>
      <div class="field">
        <label>{{ $t('profile.personal.email') }} <small>{{ $t('profile.personal.emailLocked') }}</small></label>
        <input :value="email" type="email" disabled />
      </div>
      <div class="field">
        <label>{{ $t('profile.personal.phone') }}</label>
        <input :value="modelValue.phone" @input="update('phone', $event.target.value)"
               type="tel" maxlength="40" :placeholder="$t('profile.personal.phonePlaceholder')" />
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: "PersonalDataSection",
  props: {
    modelValue: { type: Object, required: true },
    email:      { type: String, default: "" },
  },
  emits: ["update:modelValue"],
  computed: {
    computedAge() {
      if (!this.modelValue.dateOfBirth) return null;
      const dob = new Date(this.modelValue.dateOfBirth);
      if (isNaN(dob)) return null;
      const today = new Date();
      let age = today.getFullYear() - dob.getFullYear();
      const m = today.getMonth() - dob.getMonth();
      if (m < 0 || (m === 0 && today.getDate() < dob.getDate())) age--;
      return age;
    },
  },
  methods: {
    update(field, value) {
      this.$emit("update:modelValue", { ...this.modelValue, [field]: value });
    },
    ageWord(n) {
      const last = n % 10;
      const tens = n % 100;
      if (tens >= 11 && tens <= 14) return this.$t('profile.personal.yearMany');
      if (last === 1)               return this.$t('profile.personal.yearOne');
      if (last >= 2 && last <= 4)   return this.$t('profile.personal.yearFew');
      return this.$t('profile.personal.yearMany');
    },
  },
};
</script>
