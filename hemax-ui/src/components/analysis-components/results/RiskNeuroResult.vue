<template>
  <div class="result-card">
    <ResultHeader
      :type="analysis.type"
      :created-at="analysis.createdAt"
      :severity="severity"
    />

    <div v-if="topFlag" class="top-flag">
      <i class="fa-solid fa-flag"></i>
      <span>{{ topFlag }}</span>
    </div>

    <ToneBanner :tone="tone" :summary="summary" />

    <div v-if="summary && (!tone || tone === 'normal')" class="summary">
      <h4>{{ $t('results.headers.summary') }}</h4>
      <p>{{ summary }}</p>
    </div>

    <StoryCards :stories="stories" />

    <RisksList v-if="showRisks" :risks="result.risks" />

    <DoctorNote :note="doctorNote" />

    <RawJsonDisplay
      :raw-input-json="analysis.rawInputJson"
      :result-json="analysis.resultJson"
    />
  </div>
</template>

<script>
import ResultHeader   from "./shared/ResultHeader.vue";
import ToneBanner     from "./shared/ToneBanner.vue";
import StoryCards     from "./shared/StoryCards.vue";
import RisksList      from "./shared/RisksList.vue";
import DoctorNote     from "./shared/DoctorNote.vue";
import RawJsonDisplay from "./shared/RawJsonDisplay.vue";

/**
 * Renders Risk (chronic-disease screen) and Neuro (psychological screen)
 * analyses. They share a structure: probability bars + tone-driven narrative
 * + optional doctor note. No reference-range lab table.
 */
export default {
  name: "RiskNeuroResult",
  components: {
    ResultHeader, ToneBanner, StoryCards, RisksList, DoctorNote, RawJsonDisplay,
  },
  props: {
    analysis: { type: Object, required: true },
  },
  computed: {
    severity() {
      return this.analysis.severityLabel ?? this.analysis.severityName
          ?? this.analysis.severity ?? this.result.severity ?? "Unknown";
    },
    result()     { return this.analysis.result || {}; },
    topFlag()    { return this.analysis.topFlag || this.result.topFlag || null; },
    summary()    {
      return this.analysis.summaryUa || this.analysis.summary || this.result.summary || null;
    },
    tone()       { return this.result.tone || this.result.narrative?.tone || null; },
    stories()    { return this.result.stories || this.result.narrative?.stories || []; },
    doctorNote() { return this.analysis.doctorNote || null; },
    showRisks() {
      return this.result.overall_tier !== "insufficient_data"
          && this.tone !== "neutral";
    },
  },
};
</script>
