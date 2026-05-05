<template>
  <div v-if="normalised.length" class="risks">
    <h4>{{ $t('results.headers.risksList') }}</h4>
    <div
      v-for="(r, idx) in normalised"
      :key="r.label"
      :class="['risk-row', `tier-${r.tier || 'unknown'}`]"
    >
      <div class="r-head">
        <span class="r-label">{{ r.label }}</span>
        <span v-if="r.tier" class="r-tier">{{ tierLabel(r.tier) }}</span>
        <strong class="r-prob">{{ Math.round(r.probability * 100) }}%</strong>
      </div>
      <div class="bar">
        <div
          class="fill"
          :style="{ width: Math.round(r.probability * 100) + '%' }"
        ></div>
        <div
          v-if="r.baseline != null"
          class="baseline-marker"
          :style="{ left: Math.round(r.baseline * 100) + '%' }"
          :title="$t('results.populationAvg', { percent: (r.baseline * 100).toFixed(1) })"
        ></div>
      </div>
      <div v-if="r.baseline != null || r.oddsRatio != null" class="r-meta">
        <span v-if="r.baseline != null">
          {{ $t('results.populationAvg', { percent: (r.baseline * 100).toFixed(1) }) }}
        </span>
        <span v-if="r.oddsRatio != null && r.oddsRatio !== 1">
          {{ r.oddsRatio > 1
              ? $t('results.oddsHigher', { x: r.oddsRatio.toFixed(1) })
              : $t('results.oddsLower',  { x: r.oddsRatio.toFixed(1) }) }}
        </span>
      </div>

      <div
        v-if="r.topDrivers && r.topDrivers.length > 0"
        class="drivers"
      >
        <button
          type="button"
          class="drivers-toggle"
          @click="toggleDrivers(idx)"
          :aria-expanded="expanded[idx] ? 'true' : 'false'"
        >
          <i
            class="fa-solid fa-chevron-right chevron"
            :class="{ open: expanded[idx] }"
          ></i>
          <span>{{ expanded[idx]
              ? $t('results.topDrivers.hideToggle')
              : $t('results.topDrivers.toggle') }}</span>
          <span class="drivers-count">({{ r.topDrivers.length }})</span>
        </button>

        <div v-if="expanded[idx]" class="drivers-list">
          <p class="drivers-intro" v-html="introHtml(r.topDrivers.length)"></p>

          <div
            v-for="d in r.topDrivers"
            :key="d.feature"
            :class="['driver-row', directionConfig(d.direction).class]"
          >
            <i
              class="fa-solid driver-arrow"
              :class="directionConfig(d.direction).icon"
              :title="directionConfig(d.direction).label"
            ></i>
            <div class="driver-content">
              <div class="driver-head">
                <span class="driver-name">{{ featureLabel(d.feature) }}</span>
                <span v-if="d.value != null" class="driver-value">
                  {{ formatValue(d.value) }}
                </span>
              </div>
              <div class="driver-meta">
                <span class="driver-direction">
                  {{ directionConfig(d.direction).label }}
                </span>
                <span
                  v-if="d.z_score != null"
                  class="driver-z"
                  :title="$t('results.topDrivers.zScoreHint')"
                >
                  {{ $t('results.topDrivers.zScoreLabel') }} = {{ d.z_score.toFixed(1) }}
                </span>
                <span
                  v-if="d.contribution != null"
                  class="driver-mag"
                  :title="$t('results.topDrivers.contributionHint')"
                >
                  {{ $t('results.topDrivers.contributionLabel') }}: {{ Math.abs(d.contribution).toFixed(2) }}
                </span>
              </div>
            </div>
          </div>

          <p class="drivers-disclaimer">
            <i class="fa-solid fa-circle-info"></i>
            {{ $t('results.topDrivers.disclaimer') }}
          </p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import {
  tierLabel,
  featureLabel,
  directionConfig,
} from "@/constants/analysisConstants";

export default {
  name: "RisksList",
  props: {
    risks: { type: [Array, Object, null], default: null },
  },
  data() {
    return {
      expanded: {},
    };
  },
  computed: {
    normalised() {
      if (!this.risks) return [];
      if (Array.isArray(this.risks)) {
        return this.risks.map(v => ({
          label:      this.pickName(v),
          probability: v.probability ?? 0,
          tier:       v.risk_tier || null,
          baseline:   v.population_prevalence ?? null,
          oddsRatio:  v.odds_ratio_vs_baseline ?? null,
          topDrivers: v.top_drivers || [],
        }));
      }
      return Object.entries(this.risks).map(([k, v]) => ({
        label: (v && v.label) || k,
        probability: typeof v === "number" ? v : (v?.probability ?? 0),
        tier: null, baseline: null, oddsRatio: null, topDrivers: [],
      }));
    },
  },
  methods: {
    tierLabel,
    featureLabel,
    directionConfig,
    pickName(v) {
      if (this.$locale === "en") {
        return v.name_en || v.name_ua || v.target || "—";
      }
      return v.name_ua || v.name_en || v.target || "—";
    },
    introHtml(n) {
      const tpl = this.$t('results.topDrivers.intro', { n });
      const raises = this.$t('results.topDrivers.introRaisesBold');
      const lowers = this.$t('results.topDrivers.introLowersBold');
      const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
      return tpl
        .replace(new RegExp(esc(raises), 'g'), `<strong>${raises}</strong>`)
        .replace(new RegExp(esc(lowers), 'g'), `<strong>${lowers}</strong>`);
    },
    toggleDrivers(idx) {
      this.expanded = { ...this.expanded, [idx]: !this.expanded[idx] };
    },
    formatValue(v) {
      if (v == null || Number.isNaN(v)) return this.$t('results.noValue');
      const abs = Math.abs(v);
      if (abs >= 100) return Math.round(v).toString();
      if (abs >= 10)  return v.toFixed(1);
      if (abs >= 1)   return v.toFixed(2);
      return v.toFixed(3);
    },
  },
};
</script>
