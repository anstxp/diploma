<template>
  <div v-if="!dismissed" :class="['derma-warning', { compact: compact }]">
    <div class="derma-warning__icon" aria-hidden="true">⚠</div>
    <div class="derma-warning__content">
      <template v-if="compact">
        <p class="derma-warning__title">{{ t('analysis.derma.warning.compactText') }}</p>
      </template>
      <template v-else>
        <h3 class="derma-warning__title">{{ t('analysis.derma.warning.title') }}</h3>
        <p class="derma-warning__text">{{ t('analysis.derma.warning.text') }}</p>
        <ul class="derma-warning__list">
          <li v-html="li1Html"></li>
          <li>{{ t('analysis.derma.warning.li2') }}</li>
          <li>{{ t('analysis.derma.warning.li3') }}</li>
          <li v-html="li4Html"></li>
        </ul>
      </template>
    </div>
    <button
      v-if="dismissable"
      type="button"
      class="derma-warning__close"
      :aria-label="t('analysis.derma.warning.dismiss')"
      @click="dismiss"
    >×</button>
  </div>
</template>

<script setup>
import { ref, computed, inject } from 'vue';

const props = defineProps({
  compact:     { type: Boolean, default: false },
  dismissable: { type: Boolean, default: false },
  persistDismiss: { type: Boolean, default: false },
});

const i18n = inject('i18n');
const t = i18n?.t || ((key) => key);

const STORAGE_KEY = 'hemax_derma_warning_dismissed_v1';

const dismissed = ref(
  props.persistDismiss && typeof localStorage !== 'undefined'
    ? localStorage.getItem(STORAGE_KEY) === '1'
    : false
);

function dismiss() {
  dismissed.value = true;
  if (props.persistDismiss && typeof localStorage !== 'undefined') {
    try { localStorage.setItem(STORAGE_KEY, '1'); }
    catch (_) { /* Safari private mode etc. */ }
  }
}

function esc(s) {
  return String(s ?? '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
}

const li1Html = computed(() => {
  const prototype = `<strong>${esc(t('analysis.derma.warning.li1Bold'))}</strong>`;
  return t('analysis.derma.warning.li1', { prototype });
});

const li4Html = computed(() => {
  const immediately = `<strong>${esc(t('analysis.derma.warning.li4Bold'))}</strong>`;
  return t('analysis.derma.warning.li4', { immediately });
});
</script>

<style scoped>
.derma-warning {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  margin: 0 0 16px 0;
  background: #fff8e6;
  border: 1px solid #f5d97a;
  border-left: 4px solid #d4a017;
  border-radius: 6px;
  color: #5a4400;
  font-size: 14px;
  line-height: 1.45;
}

.derma-warning.compact {
  padding: 10px 14px;
  font-size: 13px;
}

.derma-warning__icon {
  flex: 0 0 auto;
  font-size: 20px;
  line-height: 1;
  margin-top: 1px;
  color: #d4a017;
}

.derma-warning__content { flex: 1 1 auto; min-width: 0; }

.derma-warning__title {
  margin: 0 0 6px 0;
  font-size: 14px;
  font-weight: 600;
  color: #5a4400;
}

.derma-warning.compact .derma-warning__title {
  margin: 0;
  font-size: 13px;
  font-weight: 500;
}

.derma-warning__text { margin: 0 0 8px 0; }
.derma-warning__list { margin: 0; padding-left: 18px; }
.derma-warning__list li { margin: 3px 0; }

.derma-warning__close {
  flex: 0 0 auto;
  background: transparent;
  border: 0;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
  color: #8a7400;
  padding: 0 4px;
  margin-left: 4px;
}

.derma-warning__close:hover { color: #5a4400; }

@media (prefers-color-scheme: dark) {
  .derma-warning {
    background: #3a2f15;
    border-color: #6e5a1f;
    border-left-color: #d4a017;
    color: #f0e0a8;
  }
  .derma-warning__title { color: #f0e0a8; }
  .derma-warning__close { color: #f0e0a8; }
}
</style>
