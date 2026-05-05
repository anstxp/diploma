<template>
  <form class="analysis-form" @submit.prevent="onSubmit">
    <div class="upload-area" :class="{ has: !!preview }" @click="triggerFile">
      <input
        ref="fileInput"
        type="file"
        accept="image/jpeg,image/png,image/webp"
        @change="onFileChange"
        style="display:none"
      />
      <img v-if="preview" :src="preview" class="preview" alt="lesion preview" />
      <div v-else class="upload-prompt">
        <i class="fa-solid fa-camera"></i>
        <span>{{ $t('analysis.derma.uploadPrompt') }}</span>
        <small>{{ $t('analysis.derma.uploadFormats') }}</small>
      </div>
    </div>

    <div class="section-title">{{ $t('analysis.derma.sectionLocalization') }}</div>
    <div class="form-grid">
      <div class="metric-row">
        <label>{{ $t('analysis.derma.locationLabel') }}</label>
        <select v-model="form.localization" class="box">
          <option value="head/neck">{{ $t('analysis.derma.localizationOptions.headNeck') }}</option>
          <option value="upper extremity">{{ $t('analysis.derma.localizationOptions.upperExtremity') }}</option>
          <option value="lower extremity">{{ $t('analysis.derma.localizationOptions.lowerExtremity') }}</option>
          <option value="torso">{{ $t('analysis.derma.localizationOptions.torso') }}</option>
          <option value="back">{{ $t('analysis.derma.localizationOptions.back') }}</option>
          <option value="chest">{{ $t('analysis.derma.localizationOptions.chest') }}</option>
          <option value="abdomen">{{ $t('analysis.derma.localizationOptions.abdomen') }}</option>
          <option value="palms/soles">{{ $t('analysis.derma.localizationOptions.palmsSoles') }}</option>
          <option value="genital">{{ $t('analysis.derma.localizationOptions.genital') }}</option>
          <option value="acral">{{ $t('analysis.derma.localizationOptions.acral') }}</option>
          <option value="unknown">{{ $t('analysis.derma.localizationOptions.unknown') }}</option>
        </select>
      </div>
      <MetricInput id="age" :label="$t('analysis.derma.ageLabel')" :unit="$t('profile.personal.yearMany')" v-model="form.age" min="0" max="120" />
      <div class="metric-row">
        <label>{{ $t('analysis.derma.sexLabel') }}</label>
        <select v-model="form.sex" class="box">
          <option value="Male">{{ $t('analysis.derma.sexMale') }}</option>
          <option value="Female">{{ $t('analysis.derma.sexFemale') }}</option>
          <option value="Unknown">{{ $t('analysis.derma.sexUnknown') }}</option>
        </select>
      </div>
    </div>


    <div class="actions">
      <button type="submit" class="btn" :disabled="loading || !file">
        {{ loading ? $t('analysis.derma.submittingButton') : $t('analysis.derma.submitButton') }}
      </button>
      <p v-if="!file" class="warning">{{ $t('analysis.derma.needFile') }}</p>
    </div>
  </form>
</template>

<script>
import MetricInput from "@/components/analysis-components/common/MetricInput.vue";

export default {
  name: "DermaForm",
  components: { MetricInput },
  props: {
    initialAge: { type: Number, default: 30 },
    initialSex: { type: String, default: "Unknown" },
  },
  emits: ["submitted"],
  data() {
    return {
      loading: false,
      file: null,
      preview: null,
      form: {
        age: this.initialAge,
        sex: this.initialSex,
        localization: "back",
      },
    };
  },
  methods: {
    triggerFile() {
      this.$refs.fileInput.click();
    },
    async onFileChange(e) {
      const f = e.target.files?.[0];
      e.target.value = "";
      if (!f) return;

      const { validateImage, checkImageMagicBytes } =
        await import("@/utils/validation");

      const err = validateImage(f, 10 * 1024 * 1024); // 10 MB
      if (err) {
        this.$store.dispatch("flash", { type: "error", message: err });
        return;
      }
      if (!(await checkImageMagicBytes(f))) {
        this.$store.dispatch("flash", {
          type: "error",
          message: this.$t('analysis.derma.errorBadImage'),
        });
        return;
      }

      this.file = f;
      const reader = new FileReader();
      reader.onload = (ev) => { this.preview = ev.target.result; };
      reader.readAsDataURL(f);
    },
    async onSubmit() {
      if (!this.file) return;
      this.loading = true;
      try {
        const fd = new FormData();
        fd.append("file", this.file);
        fd.append("language", this.$locale);
        Object.entries(this.form).forEach(([k, v]) => fd.append(k, v));
        const result = await this.$store.dispatch("analyses/submit", {
          kind: "derma", payload: fd, language: this.$locale,
        });
        this.$emit("submitted", result);
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('analysis.derma.errorSubmit'),
        });
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
.analysis-form {
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 2rem;
}

.upload-area {
  border: 2px dashed rgba(65, 90, 119, 0.3);
  border-radius: 0.6rem;
  padding: 3rem 2rem;
  text-align: center;
  cursor: pointer;
  margin-bottom: 2rem;
  transition: all 0.2s;
  background: rgba(65, 90, 119, 0.02);

  &:hover {
    border-color: var(--purple);
    background: rgba(65, 90, 119, 0.06);
  }

  &.has { padding: 1rem; border-style: solid; border-color: var(--purple); }

  .upload-prompt {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.6rem;

    i { font-size: 3.6rem; color: var(--purple); }
    span { font-size: 1.4rem; color: var(--black); text-transform: none; }
    small { font-size: 1.2rem; color: var(--light-color); text-transform: none; }
  }

  .preview { max-width: 100%; max-height: 36rem; border-radius: 0.4rem; }
}

.section-title {
  font-size: 1.3rem;
  text-transform: uppercase;
  letter-spacing: 0.1rem;
  color: var(--purple);
  font-weight: 600;
  margin: 1.5rem 0 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(65, 90, 119, 0.2);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(28rem, 1fr));
  gap: 0 2rem;
}

.metric-row {
  display: grid;
  grid-template-columns: 1fr 14rem;
  gap: 1rem;
  align-items: center;
  padding: 1rem 0;
  border-bottom: 1px solid rgba(0,0,0,0.05);

  label { font-size: 1.4rem; text-transform: none; color: var(--black); }
  .box { width: 100%; padding: 0.7rem 1rem; font-size: 1.4rem; border: var(--border); border-radius: 0.4rem; }
}

.actions {
  margin-top: 2rem;
  text-align: center;

  .warning {
    margin-top: 0.6rem;
    color: #854F0B;
    font-size: 1.2rem;
    text-transform: none;
  }
}
</style>
