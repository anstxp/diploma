<template>
  <div>
    <PdfUploadCard
      hint="chem"
      @extracted="onPdfExtracted"
      @reset="onPdfReset"
    />

    <form class="analysis-form" @submit.prevent="onSubmit">
      <fieldset class="form-section">
        <legend>{{ $t('analysis.chem.sectionGlucose') }}</legend>
        <div class="form-grid">
          <MetricInput id="glucose" :label="$t('analysis.chem.labels.glucose')" unit="ммоль/л" v-model="form.glucose" />
          <MetricInput id="a1c"     :label="$t('analysis.chem.labels.a1c')"     unit="%"       v-model="form.a1c" />
        </div>
      </fieldset>

      <fieldset class="form-section">
        <legend>{{ $t('analysis.chem.sectionKidneys') }}</legend>
        <div class="form-grid">
          <MetricInput id="creatinine" :label="$t('analysis.chem.labels.creatinine')" unit="мкмоль/л" v-model="form.creatinine" />
          <MetricInput id="urea"       :label="$t('analysis.chem.labels.urea')"        unit="ммоль/л"  v-model="form.urea" />
          <MetricInput id="uric_acid"  :label="$t('analysis.chem.labels.uricAcid')"    unit="мкмоль/л" v-model="form.uric_acid" />
        </div>
      </fieldset>

      <fieldset class="form-section">
        <legend>{{ $t('analysis.chem.sectionLiverBile') }}</legend>
        <div class="form-grid">
          <MetricInput id="alt"              :label="$t('analysis.chem.labels.alt')"              unit="U/L"      v-model="form.alt" />
          <MetricInput id="ast"              :label="$t('analysis.chem.labels.ast')"              unit="U/L"      v-model="form.ast" />
          <MetricInput id="alp"              :label="$t('analysis.chem.labels.alp')"              unit="U/L"      v-model="form.alp" />
          <MetricInput id="ggt"              :label="$t('analysis.chem.labels.ggt')"              unit="U/L"      v-model="form.ggt" />
          <MetricInput id="bilirubin_total"  :label="$t('analysis.chem.labels.bilirubinTotal')"   unit="мкмоль/л" v-model="form.bilirubin_total" />
          <MetricInput id="bilirubin_direct" :label="$t('analysis.chem.labels.bilirubinDirect')"  unit="мкмоль/л" v-model="form.bilirubin_direct" />
        </div>
      </fieldset>

      <fieldset class="form-section">
        <legend>{{ $t('analysis.chem.sectionProtein') }}</legend>
        <div class="form-grid">
          <MetricInput id="total_protein" :label="$t('analysis.chem.labels.totalProtein')" unit="г/л" v-model="form.total_protein" />
          <MetricInput id="albumin"       :label="$t('analysis.chem.labels.albumin')"     unit="г/л" v-model="form.albumin" />
        </div>
      </fieldset>

      <fieldset class="form-section">
        <legend>{{ $t('analysis.chem.sectionLipids') }}</legend>
        <div class="form-grid">
          <MetricInput id="cholesterol"   :label="$t('analysis.chem.labels.cholesterol')"   unit="ммоль/л" v-model="form.cholesterol_total" />
          <MetricInput id="hdl"           :label="$t('analysis.chem.labels.hdl')"           unit="ммоль/л" v-model="form.hdl" />
          <MetricInput id="ldl"           :label="$t('analysis.chem.labels.ldl')"           unit="ммоль/л" v-model="form.ldl" />
          <MetricInput id="triglycerides" :label="$t('analysis.chem.labels.triglycerides')" unit="ммоль/л" v-model="form.triglycerides" />
        </div>
      </fieldset>

      <fieldset class="form-section">
        <legend>{{ $t('analysis.chem.sectionElectrolytes') }}</legend>
        <div class="form-grid">
          <MetricInput id="sodium"      :label="$t('analysis.chem.labels.sodium')"      unit="ммоль/л" v-model="form.sodium" />
          <MetricInput id="potassium"   :label="$t('analysis.chem.labels.potassium')"   unit="ммоль/л" v-model="form.potassium" />
          <MetricInput id="chloride"    :label="$t('analysis.chem.labels.chloride')"    unit="ммоль/л" v-model="form.chloride" />
          <MetricInput id="bicarbonate" :label="$t('analysis.chem.labels.bicarbonate')" unit="ммоль/л" v-model="form.bicarbonate" />
        </div>
      </fieldset>

      <fieldset class="form-section">
        <legend>{{ $t('analysis.chem.sectionMinerals') }}</legend>
        <div class="form-grid">
          <MetricInput id="calcium"   :label="$t('analysis.chem.labels.calcium')"   unit="ммоль/л" v-model="form.calcium" />
          <MetricInput id="magnesium" :label="$t('analysis.chem.labels.magnesium')" unit="ммоль/л" v-model="form.magnesium" />
          <MetricInput id="phosphate" :label="$t('analysis.chem.labels.phosphate')" unit="ммоль/л" v-model="form.phosphate" />
        </div>
      </fieldset>

      <fieldset class="form-section">
        <legend>{{ $t('analysis.chem.sectionIron') }}</legend>
        <p class="section-hint">{{ $t('analysis.chem.sectionIronHint') }}</p>
        <div class="form-grid">
          <MetricInput id="iron"     :label="$t('analysis.chem.labels.iron')"     unit="мкмоль/л" v-model="form.iron" />
          <MetricInput id="ferritin" :label="$t('analysis.chem.labels.ferritin')" unit="нг/мл"    v-model="form.ferritin" />
          <MetricInput id="tibc"     :label="$t('analysis.chem.labels.tibc')"     unit="мкмоль/л" v-model="form.tibc" />
          <MetricInput id="tsat"     :label="$t('analysis.chem.labels.tsat')"     unit="%"        v-model="form.tsat" />
        </div>
      </fieldset>

      <fieldset class="form-section">
        <legend>{{ $t('analysis.chem.sectionOther') }}</legend>
        <p class="section-hint">{{ $t('analysis.chem.sectionOtherHint') }}</p>
        <div class="form-grid">
          <MetricInput id="crp"       :label="$t('analysis.chem.labels.crp')"       unit="мг/л"  v-model="form.crp" />
          <MetricInput id="amylase"   :label="$t('analysis.chem.labels.amylase')"   unit="U/L"   v-model="form.amylase" />
          <MetricInput id="lipase"    :label="$t('analysis.chem.labels.lipase')"    unit="U/L"   v-model="form.lipase" />
          <MetricInput id="ck"        :label="$t('analysis.chem.labels.ck')"        unit="U/L"   v-model="form.ck" />
          <MetricInput id="ldh"       :label="$t('analysis.chem.labels.ldh')"       unit="U/L"   v-model="form.ldh" />
          <MetricInput id="vitd_25oh" :label="$t('analysis.chem.labels.vitd_25oh')" unit="нг/мл" v-model="form.vitd_25oh" />
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
  glucose: "glucose", a1c: "a1c",
  creatinine: "creatinine", urea: "urea", uric_acid: "uric_acid",
  alt: "alt", ast: "ast", alp: "alp", ggt: "ggt",
  bilirubin_total: "bilirubin_total", bilirubin_direct: "bilirubin_direct",
  protein_total: "total_protein", albumin: "albumin",
  cholesterol_total: "cholesterol_total",
  hdl: "hdl", ldl: "ldl", triglycerides: "triglycerides",
  sodium: "sodium", potassium: "potassium",
  chloride: "chloride", bicarbonate: "bicarbonate",
  calcium: "calcium", magnesium: "magnesium", phosphate: "phosphate",
  iron: "iron", ferritin: "ferritin", tibc: "tibc", tsat: "tsat",
  crp: "crp", amylase: "amylase", lipase: "lipase",
  ck: "ck", ldh: "ldh", vitd_25oh: "vitd_25oh",
};

export default {
  mixins: [profilePrefillMixin],
  name: "ChemForm",
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
      form: this.emptyForm(),
    };
  },
  methods: {
    emptyForm() {
      return {
        glucose: null, a1c: null,
        creatinine: null, urea: null, uric_acid: null,
        alt: null, ast: null, alp: null, ggt: null,
        bilirubin_total: null, bilirubin_direct: null,
        total_protein: null, albumin: null,
        cholesterol_total: null, hdl: null, ldl: null, triglycerides: null,
        sodium: null, potassium: null, chloride: null, bicarbonate: null,
        calcium: null, magnesium: null, phosphate: null,
        iron: null, ferritin: null, tibc: null, tsat: null,
        crp: null, amylase: null, lipase: null, ck: null, ldh: null,
        vitd_25oh: null,
        age: this.initialAge,
        sex: this.initialSex !== "Unknown" ? this.initialSex : "Female",
      };
    },
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
            "chem", this.form, this.pdfFileAssetId, this.$locale
          );
          result = data;
          this.$store.dispatch("flash", {
            type: "success",
            message: this.$t('analysis.flashSubmittedFromPdf'),
          });
        } else {
          result = await this.$store.dispatch("analyses/submit", {
            kind: "chem", payload: this.form, language: this.$locale,
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
  .btn:disabled { opacity: 0.5; cursor: not-allowed; }
}
</style>
