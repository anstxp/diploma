<template>
  <form class="analysis-form" @submit.prevent="onSubmit">
    <div class="section-title">{{ $t('analysis.risk.sectionDemo') }}</div>
    <div class="form-grid">
      <MetricInput id="age" :label="$t('analysis.risk.ageLabel')" :unit="$t('profile.personal.yearMany')" v-model="form.age" min="18" max="100" />
      <div class="metric-row">
        <label>{{ $t('analysis.risk.sexLabel') }}</label>
        <select v-model="form.sex" class="box">
          <option value="Male">{{ $t('analysis.risk.sexMale') }}</option>
          <option value="Female">{{ $t('analysis.risk.sexFemale') }}</option>
        </select>
      </div>
      <MetricInput id="height" :label="$t('analysis.risk.heightLabel')" unit="см" v-model="form.height_cm" min="100" max="250" />
      <MetricInput id="weight" :label="$t('analysis.risk.weightLabel')" unit="кг" v-model="form.weight_kg" min="20" max="300" />
    </div>

    <div class="section-title">{{ $t('analysis.risk.sectionVitals') }}</div>
    <div class="form-grid">
      <MetricInput id="systolic" :label="$t('analysis.risk.sbpLabel')" unit="мм рт.ст." v-model="form.systolic_bp" />
      <MetricInput id="diastolic" :label="$t('analysis.risk.dbpLabel')" unit="мм рт.ст." v-model="form.diastolic_bp" />
      <MetricInput id="heart_rate" :label="$t('analysis.risk.heartRateLabel')" unit="уд/хв" v-model="form.heart_rate" />
      <MetricInput id="glucose" :label="$t('analysis.risk.glucoseLabel')" unit="ммоль/л" v-model="form.fasting_glucose" />
      <MetricInput id="hba1c" :label="$t('analysis.risk.hba1cLabel')" unit="%" v-model="form.hba1c" />
      <MetricInput id="cholesterol" :label="$t('analysis.risk.cholesterolLabel')" unit="ммоль/л" v-model="form.cholesterol_total" />
    </div>

    <div class="section-title">{{ $t('analysis.risk.sectionLifestyle') }}</div>
    <div class="form-grid lifestyle">
      <label class="checkbox">
        <input type="checkbox" v-model="form.smoker" /> {{ $t('analysis.risk.smoker') }}
      </label>
      <label class="checkbox">
        <input type="checkbox" v-model="form.alcohol_regular" /> {{ $t('analysis.risk.alcoholRegular') }}
      </label>
      <label class="checkbox">
        <input type="checkbox" v-model="form.physical_activity_low" /> {{ $t('analysis.risk.physicalActivityLow') }}
      </label>
      <label class="checkbox">
        <input type="checkbox" v-model="form.family_history_diabetes" /> {{ $t('analysis.risk.familyHistoryDiabetes') }}
      </label>
      <label class="checkbox">
        <input type="checkbox" v-model="form.family_history_cvd" /> {{ $t('analysis.risk.familyHistoryCvd') }}
      </label>
    </div>

    <div class="merge-option">
      <label>
        <input type="checkbox" v-model="mergeRecentLabs" />
        <span>
          {{ $t('analysis.risk.mergeLabsTitle') }}
          <small>{{ $t('analysis.risk.mergeLabsHelp') }}</small>
        </span>
      </label>
    </div>

    <div class="actions">
      <button type="submit" class="btn" :disabled="loading">
        {{ loading ? $t('analysis.risk.submittingButton') : $t('analysis.risk.submitButton') }}
      </button>
    </div>
  </form>
</template>

<script>
import profilePrefillMixin from "@/mixins/profilePrefill.js";
import MetricInput from "@/components/analysis-components/common/MetricInput.vue";

export default {
  mixins: [profilePrefillMixin],
  name: "RiskForm",
  components: { MetricInput },
  props: {
    initialAge: { type: Number, default: 30 },
    initialSex: { type: String, default: "Female" },
  },
  emits: ["submitted"],
  data() {
    return {
      loading: false,
      mergeRecentLabs: true,
      form: {
        age: this.initialAge,
        sex: this.initialSex !== "Unknown" ? this.initialSex : "Female",
        height_cm: null, weight_kg: null,
        systolic_bp: null, diastolic_bp: null,
        heart_rate: null, fasting_glucose: null, hba1c: null,
        cholesterol_total: null,
        smoker: false,
        alcohol_regular: false,
        physical_activity_low: false,
        family_history_diabetes: false,
        family_history_cvd: false,
      },
    };
  },
  methods: {
    buildPayload() {
      const f = this.form;
      const payload = {
        age: f.age,
        sex: f.sex,
      };

      if (f.height_cm != null && f.weight_kg != null
          && f.height_cm > 0 && f.weight_kg > 0) {
        const hm = Number(f.height_cm) / 100;
        payload.bmi = Number((Number(f.weight_kg) / (hm * hm)).toFixed(1));
      }

      // Vitals — canonical names.
      if (f.systolic_bp  != null) payload.sbp   = Number(f.systolic_bp);
      if (f.diastolic_bp != null) payload.dbp   = Number(f.diastolic_bp);
      if (f.heart_rate   != null) payload.pulse = Number(f.heart_rate);

      // Labs — must be nested in `labs: {}`.
      const labs = {};
      if (f.fasting_glucose    != null) labs.glucose = Number(f.fasting_glucose);
      if (f.hba1c              != null) labs.a1c     = Number(f.hba1c);
      if (f.cholesterol_total  != null) labs.tchol   = Number(f.cholesterol_total);
      if (Object.keys(labs).length > 0) payload.labs = labs;

      const clinical = {};
      if (f.smoker)                  clinical.smoker          = true;
      if (f.alcohol_regular)         clinical.alcohol_regular = true;
      if (f.physical_activity_low)   clinical.sedentary       = true;
      if (f.family_history_diabetes) clinical.family_diabetes = true;
      if (f.family_history_cvd)      clinical.family_cvd      = true;
      if (Object.keys(clinical).length > 0) {
        payload.context = { clinical };
      }

      return payload;
    },
    async onSubmit() {
      this.loading = true;
      try {
        const payload = this.buildPayload();
        const result = await this.$store.dispatch("analyses/submit", {
          kind: "risk", payload,
          mergeRecentLabs: this.mergeRecentLabs,
          language: this.$locale,
        });
        this.$emit("submitted", result);
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('analysis.risk.errorSubmit'),
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
.form-grid.lifestyle {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(22rem, 1fr));
  gap: 1rem;
  padding: 1rem 0;
}
.checkbox {
  display: flex;
  align-items: center;
  gap: 0.6rem;
  font-size: 1.4rem;
  color: var(--black);
  text-transform: none;
  cursor: pointer;

  input[type="checkbox"] {
    width: 1.6rem;
    height: 1.6rem;
    accent-color: var(--purple);
    cursor: pointer;
  }
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
.actions { margin-top: 2rem; text-align: center; }

.merge-option {
  margin: 1.5rem 0 0;
  padding: 1.2rem 1.4rem;
  background: rgba(65, 90, 119, 0.05);
  border: 1px solid rgba(65, 90, 119, 0.15);
  border-radius: 0.5rem;

  label {
    display: flex;
    gap: 0.8rem;
    align-items: flex-start;
    cursor: pointer;

    input[type="checkbox"] {
      margin-top: 0.3rem;
      flex-shrink: 0;
      width: 1.6rem;
      height: 1.6rem;
      accent-color: var(--purple);
      cursor: pointer;
    }

    span {
      font-size: 1.3rem;
      color: var(--black);
      text-transform: none;
      line-height: 1.5;

      small {
        display: block;
        font-size: 1.15rem;
        color: var(--light-color);
        margin-top: 0.3rem;
        line-height: 1.4;
      }
    }
  }
}
</style>
