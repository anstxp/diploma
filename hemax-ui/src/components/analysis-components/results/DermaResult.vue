<template>
  <div class="result-card">
    <ResultHeader
      :type="analysis.type"
      :created-at="analysis.createdAt"
      :severity="severity"
    />

    <!-- Lesion image hero -->
    <div v-if="analysis.fileUrl" class="lesion-image">
      <img :src="analysis.fileUrl" :alt="analysis.fileName || $t('results.derma.imageAlt')" />
      <small v-if="analysis.fileName" class="image-caption">
        <i class="fa-solid fa-image"></i> {{ analysis.fileName }}
      </small>
    </div>

    <div v-if="dermaResult" class="derma-summary">
      <div class="derma-top">
        <div class="top-class">
          <div class="t-label">{{ $t('results.derma.topClassLabel') }}</div>
          <div class="t-name">{{ topClassName }}</div>
          <div class="t-code">{{ dermaResult.top_class }}</div>
        </div>
        <div class="confidence-block">
          <div class="t-label">{{ $t('results.derma.confidenceLabel') }}</div>
          <div class="confidence-value" :class="confidenceClass">
            {{ Math.round(dermaResult.confidence * 100) }}%
          </div>
          <div class="confidence-hint">{{ confidenceHint }}</div>
        </div>
      </div>

      <div v-if="dermaResult.top_k && dermaResult.top_k.length" class="topk">
        <h4>{{ $t('results.derma.topKHeader', { n: dermaResult.top_k.length }) }}</h4>
        <div
          v-for="(c, i) in dermaResult.top_k"
          :key="c.class_code"
          :class="['topk-row', i === 0 && 'is-top']"
        >
          <div class="r-head">
            <span class="r-name">
              <span class="r-num">{{ i + 1 }}</span>
              {{ topKClassName(c) }}
              <small>({{ c.class_code }})</small>
            </span>
            <strong>{{ Math.round(c.probability * 100) }}%</strong>
          </div>
          <div class="bar">
            <div class="fill" :style="{ width: Math.round(c.probability * 100) + '%' }"></div>
          </div>
        </div>
      </div>

      <details v-if="dermaResult.all_probabilities" class="all-probs">
        <summary>{{ $t('results.derma.allProbsToggle') }}</summary>
        <div class="all-list">
          <div
            v-for="[code, prob] in sortedAllProbs"
            :key="code"
            class="prob-row"
          >
            <span class="p-code">{{ code }}</span>
            <span class="p-name">{{ dermaClassName(code) }}</span>
            <span class="p-bar">
              <span class="p-fill" :style="{ width: Math.round(prob * 100) + '%' }"></span>
            </span>
            <span class="p-val">{{ (prob * 100).toFixed(1) }}%</span>
          </div>
        </div>
      </details>

      <div class="medical-disclaimer">
        <i class="fa-solid fa-circle-info"></i>
        <p v-html="disclaimerHtml"></p>
      </div>
    </div>

    <DoctorNote :note="doctorNote" />

    <RawJsonDisplay
      :raw-input-json="analysis.rawInputJson"
      :result-json="analysis.resultJson"
    />
  </div>
</template>

<script>
import ResultHeader   from "./shared/ResultHeader.vue";
import DoctorNote     from "./shared/DoctorNote.vue";
import RawJsonDisplay from "./shared/RawJsonDisplay.vue";
import { dermaClassName } from "@/constants/analysisConstants";

export default {
  name: "DermaResult",
  components: { ResultHeader, DoctorNote, RawJsonDisplay },
  props: {
    analysis: { type: Object, required: true },
  },
  computed: {
    severity() {
      return this.analysis.severityLabel ?? this.analysis.severityName
          ?? this.analysis.severity ?? this.dermaResult?.severity ?? "Unknown";
    },
    dermaResult() { return this.analysis.result || null; },
    sortedAllProbs() {
      const ap = this.dermaResult?.all_probabilities;
      if (!ap) return [];
      return Object.entries(ap).sort((a, b) => b[1] - a[1]);
    },
    topClassName() {
      const code = this.dermaResult?.top_class;
      if (!code) return "—";
      const localized = dermaClassName(code);
      if (localized && !localized.startsWith("results.dermaClass.")) return localized;
      return this.dermaResult.top_class_name || code;
    },
    confidenceClass() {
      const c = this.dermaResult?.confidence || 0;
      if (c >= 0.7) return "high";
      if (c >= 0.4) return "mid";
      return "low";
    },
    confidenceHint() {
      const c = this.dermaResult?.confidence || 0;
      if (c >= 0.7) return this.$t('results.derma.confidenceHigh');
      if (c >= 0.4) return this.$t('results.derma.confidenceMid');
      return this.$t('results.derma.confidenceLow');
    },
    doctorNote() { return this.analysis.doctorNote || null; },
    disclaimerHtml() {
      const tpl  = this.$t('results.derma.medicalDisclaimer');
      const bold = this.$t('results.derma.medicalDisclaimerBold');
      const esc = (s) => String(s).replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      const safeBold = String(bold)
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
      return tpl.replace(new RegExp(esc(bold), 'g'), `<strong>${safeBold}</strong>`);
    },
  },
  methods: {
    dermaClassName,
    topKClassName(c) {
      const localized = dermaClassName(c.class_code);
      if (localized && !localized.startsWith("results.dermaClass.")) return localized;
      return c.class_name || c.class_code;
    },
  },
};
</script>
