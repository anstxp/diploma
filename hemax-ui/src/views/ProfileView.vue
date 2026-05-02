<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page profile-page">
    <header class="page-head">
      <h1>{{ $t('profile.title') }}</h1>
      <p class="hint">{{ $t('profile.hint') }}</p>
    </header>

    <div v-if="loading && !profile" class="loading">{{ $t('profile.loadingText') }}</div>

    <form v-else-if="profile" class="profile-form" @submit.prevent="save">
      <AvatarSection         :profile="profile" @changed="loadProfile" />
      <PersonalDataSection   v-model="form" :email="profile.email" />
      <AnthropometricsSection v-model="form" />
      <VitalsSection         v-model="form" />
      <MedicalHistorySection v-model="form" />
      <LifestyleSection      v-model="form" />
      <EmergencyContactSection v-model="form" />
      <SettingsSection       v-model="form" />

      <div class="actions">
        <button type="submit" class="btn primary" :disabled="loading">
          {{ loading ? $t('profile.saving') : $t('profile.saveButton') }}
        </button>
        <button type="button" class="btn ghost" @click="resetForm" :disabled="loading">
          {{ $t('profile.resetButton') }}
        </button>
      </div>
    </form>

    <div v-else class="error">
      {{ $t('profile.errorLoad') }}
      <button class="link" @click="loadProfile">{{ $t('common.tryAgain') }}</button>
    </div>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent       from "@/components/nav-components/header/header-component.vue";
import NavbarComponent       from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent       from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";

import AvatarSection           from "@/components/profile-sections/AvatarSection.vue";
import PersonalDataSection     from "@/components/profile-sections/PersonalDataSection.vue";
import AnthropometricsSection  from "@/components/profile-sections/AnthropometricsSection.vue";
import VitalsSection           from "@/components/profile-sections/VitalsSection.vue";
import MedicalHistorySection   from "@/components/profile-sections/MedicalHistorySection.vue";
import LifestyleSection        from "@/components/profile-sections/LifestyleSection.vue";
import EmergencyContactSection from "@/components/profile-sections/EmergencyContactSection.vue";
import SettingsSection         from "@/components/profile-sections/SettingsSection.vue";

export default {
  name: "ProfileView",
  components: {
    HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent,
    AvatarSection, PersonalDataSection, AnthropometricsSection, VitalsSection,
    MedicalHistorySection, LifestyleSection, EmergencyContactSection, SettingsSection,
  },

  data() {
    return { form: this.emptyForm() };
  },

  computed: {
    profile() { return this.$store.state.profile.profile; },
    loading() { return this.$store.state.profile.loading; },
  },

  watch: {
    profile: {
      immediate: true,
      handler(v) { if (v) this.populateForm(v); },
    },
  },

  async mounted() {
    if (!this.profile) await this.loadProfile();
  },

  methods: {
    emptyForm() {
      return {
        firstName: "", lastName: "", middleName: "",
        dateOfBirth: "", sex: "Unknown", phone: "",
        heightCm: null, weightKg: null, waistCm: null,
        typicalSystolicBp: null, typicalDiastolicBp: null, typicalRestingPulse: null,
        chronicDiseases: "", allergies: "", currentMedications: "", familyHistory: "",
        smoker: false, alcoholFrequency: "Unknown", physicalActivity: "Unknown", dietType: "Unknown",
        emergencyContactName: "", emergencyContactPhone: "", emergencyContactRelation: "",
        preferredLanguage: "uk", unitsSystem: "metric",
      };
    },

    populateForm(p) {
      this.form = {
        firstName:                p.firstName  || "",
        lastName:                 p.lastName   || "",
        middleName:               p.middleName || "",
        dateOfBirth:              p.dateOfBirth || "",
        sex:                      p.sex || "Unknown",
        phone:                    p.phone || "",
        heightCm:                 p.heightCm ?? null,
        weightKg:                 p.weightKg ?? null,
        waistCm:                  p.waistCm ?? null,
        typicalSystolicBp:        p.typicalSystolicBp ?? null,
        typicalDiastolicBp:       p.typicalDiastolicBp ?? null,
        typicalRestingPulse:      p.typicalRestingPulse ?? null,
        chronicDiseases:          p.chronicDiseases || "",
        allergies:                p.allergies || "",
        currentMedications:       p.currentMedications || "",
        familyHistory:            p.familyHistory || "",
        smoker:                   p.smoker || false,
        alcoholFrequency:         p.alcoholFrequency || "Unknown",
        physicalActivity:         p.physicalActivity || "Unknown",
        dietType:                 p.dietType || "Unknown",
        emergencyContactName:     p.emergencyContactName || "",
        emergencyContactPhone:    p.emergencyContactPhone || "",
        emergencyContactRelation: p.emergencyContactRelation || "",
        preferredLanguage:        p.preferredLanguage || "uk",
        unitsSystem:              p.unitsSystem || "metric",
      };
    },

    resetForm() { if (this.profile) this.populateForm(this.profile); },

    async loadProfile() {
      try { await this.$store.dispatch("profile/fetch"); }
      catch (e) { /* error shown via flash */ }
    },

    async save() {
      const trimOrNull = v => (typeof v === "string" ? v.trim() : v) || null;
      const payload = {
        ...this.form,
        middleName:               trimOrNull(this.form.middleName),
        phone:                    trimOrNull(this.form.phone),
        chronicDiseases:          trimOrNull(this.form.chronicDiseases),
        allergies:                trimOrNull(this.form.allergies),
        currentMedications:       trimOrNull(this.form.currentMedications),
        familyHistory:            trimOrNull(this.form.familyHistory),
        emergencyContactName:     trimOrNull(this.form.emergencyContactName),
        emergencyContactPhone:    trimOrNull(this.form.emergencyContactPhone),
        emergencyContactRelation: trimOrNull(this.form.emergencyContactRelation),
      };
      if (!payload.dateOfBirth) payload.dateOfBirth = null;

      try { await this.$store.dispatch("profile/update", payload); }
      catch (e) { /* error shown via flash */ }
    },
  },
};
</script>

<style scoped lang="scss">
@use "sass:color";
$primary: #2563eb;
$danger:  #dc2626;
$warn:    #f59e0b;
$ok:      #10b981;
$muted:   #6b7280;
$border:  #e5e7eb;
$bg:      #f9fafb;

.profile-page {
  max-width: 920px;
  margin: 1rem auto 4rem;
  padding: 0 1rem;
}
.page-head h1 { margin: 0 0 .25rem; font-size: 1.6rem; }
.page-head .hint { color: $muted; margin: 0 0 1.5rem; font-size: .9rem; }

.profile-form { display: flex; flex-direction: column; gap: 1.25rem; }


::v-deep(.section) {
  background: white;
  border: 1px solid $border;
  border-radius: 8px;
  padding: 1.25rem;
  h2 {
    margin: 0 0 1rem;
    font-size: 1.1rem;
    display: flex;
    align-items: center;
    gap: .5rem;
    i { color: $primary; }
  }
  .section-hint { color: $muted; font-size: .85rem; margin: 0 0 1rem; }

  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
  .field { display: flex; flex-direction: column; gap: .35rem; }
  .field.full { grid-column: 1 / -1; }
  .field label {
    font-size: .85rem; color: $muted; font-weight: 500;
    small { font-weight: 400; color: lighten($muted, 15%); }
  }
  .field input, .field select, .field textarea {
    padding: .55rem .75rem;
    border: 1px solid $border;
    border-radius: 6px;
    font-size: .95rem;
    font-family: inherit;
    background: white;
    &:focus { outline: 2px solid rgba($primary, 0.2); border-color: $primary; }
    &:disabled { background: #f3f4f6; color: $muted; cursor: not-allowed; }
  }
  .field textarea { resize: vertical; min-height: 70px; }
  .field.checkbox label,
  .field label.checkbox {
    display: flex; align-items: center; gap: .5rem;
    input[type=checkbox] { width: 18px; height: 18px; }
  }
  .hint-line { font-size: .8rem; color: $muted; margin-top: .15rem; }
}

::v-deep(.encrypted-badge) {
  font-size: .7rem;
  padding: .15rem .5rem;
  background: rgba($ok, 0.1);
  color: $ok;
  border-radius: 4px;
  margin-left: .5rem;
  font-weight: 500;
}

::v-deep(.bmi-display .bmi-value) {
  display: flex; align-items: baseline; gap: .5rem;
  strong { font-size: 1.4rem; color: $primary; }
  small { font-size: .8rem; padding: .15rem .5rem; border-radius: 4px;
    &.ok    { background: rgba($ok, 0.1);    color: $ok; }
    &.warn  { background: rgba($warn, 0.1);  color: $warn; }
    &.alert { background: rgba($danger, 0.1); color: $danger; }
    &.low   { background: rgba(#3b82f6, 0.1); color: #3b82f6; }
    &.neutral { background: $bg; color: $muted; }
    &.muted { color: $muted; }
  }
}

/* Avatar section */
::v-deep(.avatar-section .avatar-row) {
  display: flex; gap: 1.5rem; align-items: center;
  .avatar-display {
    width: 100px; height: 100px; border-radius: 50%; overflow: hidden;
    flex-shrink: 0; background: $bg;
    img { width: 100%; height: 100%; object-fit: cover; }
    .avatar-placeholder {
      width: 100%; height: 100%; display: flex; align-items: center; justify-content: center;
      font-size: 2rem; font-weight: 600; color: $primary;
    }
  }
  .avatar-controls h2 { margin: 0 0 .25rem; }
  .avatar-actions { display: flex; gap: .5rem; margin-top: .75rem; }
  .file-btn { position: relative; cursor: pointer;
    input[type=file] { position: absolute; inset: 0; opacity: 0; cursor: pointer; }
  }
}

.actions {
  display: flex; gap: .75rem; justify-content: flex-end; padding-top: 1rem;
  .btn {
    padding: .65rem 1.5rem;
    border-radius: 6px; border: none; font-size: .95rem; cursor: pointer;
    transition: all .15s;
    &.primary { background: $primary; color: white;
      &:hover:not(:disabled) { background: color.adjust($primary, $lightness: -8%); } }
    &.ghost { background: transparent; color: $muted; border: 1px solid $border;
      &:hover:not(:disabled) { background: $bg; } }
    &:disabled { opacity: .6; cursor: not-allowed; }
  }
}

.loading, .error { text-align: center; padding: 3rem; color: $muted; }
.link { background: none; border: none; color: $primary; cursor: pointer; text-decoration: underline; }
</style>
