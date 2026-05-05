<template>
  <div v-if="visible" :class="['tone-banner', config.class]">
    <i :class="['fa-solid', config.icon]"></i>
    <div class="tone-content">
      <strong>{{ config.title }}</strong>
      <p v-if="summary">{{ summary }}</p>
    </div>
  </div>
</template>

<script>
import { toneConfig } from "@/constants/analysisConstants";

export default {
  name: "ToneBanner",
  props: {
    tone:    { type: String, default: null },
    summary: { type: String, default: null },
  },
  computed: {
    visible() { return !!this.tone && this.tone !== "normal"; },
    config()  { return toneConfig(this.tone); },
  },
};
</script>
