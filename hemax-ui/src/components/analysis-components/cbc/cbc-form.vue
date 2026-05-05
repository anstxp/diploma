<template>
  <div>
    <PdfUploadCard
      hint="cbc"
      @extracted="onPdfExtracted"
      @reset="onPdfReset"
    />

    <form class="analysis-form" @submit.prevent="onSubmit">
      <fieldset class="form-section">
        <legend>{{ $t('analysis.cbc.sectionRed') }}</legend>
        <div class="form-grid">
          <MetricInput id="rbc"  :label="$t('analysis.cbc.labels.rbc')"  unit="×10¹²/L" v-model="form.rbc" />
          <MetricInput id="hgb"  :label="$t('analysis.cbc.labels.hgb')"  unit="г/л" v-model="form.hgb" />
          <MetricInput id="hct"  :label="$t('analysis.cbc.labels.hct')"  unit="%"   v-model="form.hct" />
          <MetricInput id="mcv"  :label="$t('analysis.cbc.labels.mcv')"  unit="фл"  v-model="form.mcv" />
          <MetricInput id="mch"  :label="$t('analysis.cbc.labels.mch')"  unit="пг"  v-model="form.mch" />
          <MetricInput id="mchc" :label="$t('analysis.cbc.labels.mchc')" unit="г/л" v-model="form.mchc" />
          <MetricInput id="rdw"  :label="$t('analysis.cbc.labels.rdw')"  unit="%"   v-model="form.rdw" />
        </div>
      </fieldset>

      <fieldset class="form-section">
        <legend>{{ $t('analysis.cbc.sectionWhite') }}</legend>
        <div class="form-grid">
          <MetricInput id="wbc"   :label="$t('analysis.cbc.labels.wbc')"   unit="×10⁹/L" v-model="form.wbc" />
          <MetricInput id="neut"  :label="$t('analysis.cbc.labels.neut')"  unit="%" v-model="form.neut_pct" />
          <MetricInput id="lymph" :label="$t('analysis.cbc.labels.lymph')" unit="%" v-model="form.lymph_pct" />
          <MetricInput id="mono"  :label="$t('analysis.cbc.labels.mono')"  unit="%" v-model="form.mono_pct" />
          <MetricInput id="eos"   :label="$t('analysis.cbc.labels.eos')"   unit="%" v-model="form.eos_pct" />
          <MetricInput id="baso"  :label="$t('analysis.cbc.labels.baso')"  unit="%" v-model="form.baso_pct" />
        </div>
      </fieldset>

      <fieldset class="form-section">
        <legend>{{ $t('analysis.cbc.sectionAbsolute') }}</legend>
        <p class="section-hint">{{ $t('analysis.cbc.sectionAbsoluteHint') }}</p>
        <div class="form-grid">
          <MetricInput id="anc" :label="$t('analysis.cbc.labels.anc')" unit="×10⁹/L" v-model="form.anc" />
          <MetricInput id="alc" :label="$t('analysis.cbc.labels.alc')" unit="×10⁹/L" v-model="form.alc" />
          <MetricInput id="amc" :label="$t('analysis.cbc.labels.amc')" unit="×10⁹/L" v-model="form.amc" />
          <MetricInput id="aec" :label="$t('analysis.cbc.labels.aec')" unit="×10⁹/L" v-model="form.aec" />
          <MetricInput id="abc" :label="$t('analysis.cbc.labels.abc')" unit="×10⁹/L" v-model="form.abc" />
        </div>
      </fieldset>

      <fieldset class="form-section">
        <legend>{{ $t('analysis.cbc.sectionPlatelets') }}</legend>
        <div class="form-grid">
          <MetricInput id="plt" :label="$t('analysis.cbc.labels.plt')" unit="×10⁹/L" v-model="form.plt" />
          <MetricInput id="mpv" :label="$t('analysis.cbc.labels.mpv')" unit="фл"     v-model="form.mpv" />
          <MetricInput id="esr" :label="$t('analysis.cbc.labels.esr')" unit="мм/год" v-model="form.esr" />
        </div>
      </fieldset>

      <div class="form-meta">
        <div class="form-row">
          <label>{{ $t('analysis.cbc.sexLabel') }}</label>
          <select v-model="form.sex" class="box">
            <option value="Male">{{ $t('analysis.cbc.sexMale') }}</option>
            <option value="Female">{{ $t('analysis.cbc.sexFemale') }}</option>
          </select>
        </div>
        <div class="form-row">
          <label>{{ $t('analysis.cbc.ageLabel') }}</label>
          <input v-model.number="form.age" type="number" min="0" max="120" class="box" />
        </div>
      </div>

      <div class="actions">
        <button type="submit" class="btn" :disabled="loading">
          {{ loading ? $t('analysis.submittingButton') : $t('analysis.submitButton') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
import profilePrefillMixin from "@/mixins/profilePrefill.js";
import MetricInput from "@/components/analysis-components/common/MetricInput.vue";
import PdfUploadCard from "@/components/analysis-components/common/PdfUploadCard.vue";
import analysesApi from "@/api/analyses";

const PDF_TO_FORM = {
  wbc: "wbc", rbc: "rbc", hgb: "hgb", hct: "hct", mcv: "mcv",
  mch: "mch", mchc: "mchc", rdw: "rdw", plt: "plt", mpv: "mpv",
  neu: "neut_pct", lym: "lymph_pct", mon: "mono_pct",
  eos: "eos_pct", bas: "baso_pct",
  anc: "anc", alc: "alc", amc: "amc", aec: "aec", abc: "abc",
  esr: "esr",
};

export default {
  mixins: [profilePrefillMixin],
  name: "CbcForm",
  components: { MetricInput, PdfUploadCard },
  props: {
    initialAge: { type: Number, default: 30 },
    initialSex: { type: String, default: "Unknown" },
  },
  emits: ["submitted"],
  data() {
    return {
      loading: false,
      pdfFileAssetId: null,
      form: {
        wbc: null, rbc: null, hgb: null, hct: null, mcv: null,
        mch: null, mchc: null, rdw: null, plt: null, mpv: null,
        neut_pct: null, lymph_pct: null, mono_pct: null,
        eos_pct: null, baso_pct: null,
        anc: null, alc: null, amc: null, aec: null, abc: null,
        esr: null,
        age: this.initialAge,
        sex: this.initialSex !== "Unknown" ? this.initialSex : "Female",
      },
    };
  },
  methods: {
    onPdfExtracted(extraction) {
      this.pdfFileAssetId = extraction.pdfFileAssetId;
      Object.entries(extraction.values).forEach(([code, value]) => {
        const fieldName = PDF_TO_FORM[code];
        if (fieldName && fieldName in this.form) {
          this.form[fieldName] = value;
        }
      });
    },
    onPdfReset() {
      this.pdfFileAssetId = null;
    },
    async onSubmit() {
      this.loading = true;
      try {
        let result;
        if (this.pdfFileAssetId) {
          const { data } = await analysesApi.submitFromPdf(
            "cbc", this.form, this.pdfFileAssetId, this.$locale
          );
          result = data;
          this.$store.dispatch("flash", {
            type: "success",
            message: this.$t('analysis.flashSubmittedFromPdf'),
          });
        } else {
          result = await this.$store.dispatch("analyses/submit", {
            kind: "cbc", payload: this.form, language: this.$locale,
          });
        }
        this.$emit("submitted", result);
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('analysis.errorSubmit'),
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

.form-section {
  border: 1px solid var(--purple-light, #d8d8e8);
  border-radius: 0.5rem;
  padding: 1.2rem 1.5rem 0.5rem;
  margin-bottom: 1.5rem;

  legend {
    padding: 0 0.6rem;
    font-size: 1.2rem;
    font-weight: 500;
    color: var(--purple);
    text-transform: uppercase;
    letter-spacing: 0.05rem;
  }

  .section-hint {
    font-size: 1.1rem;
    color: var(--gray, #6b7280);
    margin: 0 0 1rem;
  }
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(20rem, 1fr));
  gap: 1.2rem;
  margin-bottom: 1rem;
}

.form-meta {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.2rem;
  padding-top: 1.5rem;
  border-top: var(--border);
  margin-bottom: 1.5rem;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;

  label {
    font-size: 1.2rem;
    color: var(--purple);
    text-transform: uppercase;
    letter-spacing: 0.05rem;
    font-weight: 500;
  }

  .box {
    width: 100%;
    padding: 0.7rem 1rem;
    border: var(--border);
    border-radius: 0.4rem;
    font-size: 1.4rem;
    color: var(--black);
    font-family: inherit;

    &:focus { outline: none; border-color: var(--purple); }
  }
}

.actions {
  text-align: right;

  .btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

@media (max-width: 600px) {
  .form-meta { grid-template-columns: 1fr; }
}
</style>
