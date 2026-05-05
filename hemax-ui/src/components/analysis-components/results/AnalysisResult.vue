<template>
  <component :is="resultComponent" :analysis="analysis" />
</template>

<script>
import CbcChemResult  from "./CbcChemResult.vue";
import RiskNeuroResult from "./RiskNeuroResult.vue";
import DermaResult    from "./DermaResult.vue";
import { normalizeKindCode } from "@/constants/analysisConstants";

const RESULT_COMPONENT_MAP = {
  cbc:   CbcChemResult,
  chem:  CbcChemResult,
  risk:  RiskNeuroResult,
  neuro: RiskNeuroResult,
  derma: DermaResult,
};

export default {
  name: "AnalysisResult",
  props: {
    analysis: { type: Object, required: true },
  },
  computed: {
    resultComponent() {
      const code = normalizeKindCode(this.analysis.type);
      return RESULT_COMPONENT_MAP[code] || CbcChemResult;
    },
  },
};
</script>
