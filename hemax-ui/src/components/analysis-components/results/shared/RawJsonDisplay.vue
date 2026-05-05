<template>
  <details v-if="text" class="raw-json">
    <summary>{{ $t('results.headers.rawData') }}</summary>
    <pre>{{ text }}</pre>
  </details>
</template>

<script>
export default {
  name: "RawJsonDisplay",
  props: {
    rawInputJson: { type: String, default: null },
    resultJson:   { type: String, default: null },
  },
  computed: {
    text() {
      const blocks = [];
      if (this.rawInputJson) blocks.push("INPUT:\n"  + this.formatJson(this.rawInputJson));
      if (this.resultJson)   blocks.push("RESULT:\n" + this.formatJson(this.resultJson));
      return blocks.join("\n\n");
    },
  },
  methods: {
    formatJson(s) {
      try { return JSON.stringify(JSON.parse(s), null, 2); }
      catch { return s; }
    },
  },
};
</script>
