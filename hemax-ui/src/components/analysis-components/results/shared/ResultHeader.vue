<template>
  <div class="result-header">
    <div class="result-meta">
      <span class="result-kind">{{ kindLabel }}</span>
      <span class="result-date">{{ formattedDate }}</span>
    </div>
    <SeverityBadge :severity="severity" />
  </div>
</template>

<script>
import SeverityBadge from "@/components/analysis-components/common/SeverityBadge.vue";
import { kindLabel } from "@/constants/analysisConstants";

export default {
  name: "ResultHeader",
  components: { SeverityBadge },
  props: {
    type:      { type: [String, Number], required: true },
    createdAt: { type: String, default: null },
    severity:  { type: String, default: "Unknown" },
  },
  computed: {
    kindLabel() { return kindLabel(this.type); },
    formattedDate() {
      if (!this.createdAt) return "";
      const lang = this.$locale === "en" ? "en-US" : "uk-UA";
      return new Date(this.createdAt).toLocaleString(lang,
        { dateStyle: "medium", timeStyle: "short" });
    },
  },
};
</script>
