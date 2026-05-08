import { reactive, computed, watch } from 'vue';
import uk from './uk.json';
import en from './en.json';

const LOCALES = { uk, en };
const STORAGE_KEY = 'hemax-locale';
const DEFAULT_LOCALE = 'uk';

const state = reactive({
  current: loadInitialLocale(),
});

function loadInitialLocale() {
  if (typeof localStorage !== 'undefined') {
    const v = localStorage.getItem(STORAGE_KEY);
    if (v && LOCALES[v]) return v;
  }
  // Try browser preference next.
  if (typeof navigator !== 'undefined') {
    const browser = (navigator.language || '').toLowerCase();
    if (browser.startsWith('uk')) return 'uk';
    if (browser.startsWith('en')) return 'en';
  }
  return DEFAULT_LOCALE;
}

// Persist + reflect on <html lang="..">
watch(
  () => state.current,
  (loc) => {
    try {
      localStorage.setItem(STORAGE_KEY, loc);
    } catch (_) {
    }
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('lang', loc);
    }
  },
  { immediate: true }
);


export function getLocale() {
  return state.current;
}

export function setLocale(loc) {
  if (!LOCALES[loc]) {
    console.warn(`[i18n] Unknown locale: ${loc}`);
    return;
  }
  state.current = loc;
}

export function availableLocales() {
  return Object.keys(LOCALES);
}

export function t(key, params = {}) {
  const dict = LOCALES[state.current] || LOCALES[DEFAULT_LOCALE];
  if (!key) return '';
  const value = key.split('.').reduce(
    (o, k) => (o != null && typeof o === 'object' ? o[k] : undefined),
    dict
  );
  if (typeof value !== 'string') {
    if (state.current !== DEFAULT_LOCALE) {
      const fallback = key.split('.').reduce(
        (o, k) => (o != null && typeof o === 'object' ? o[k] : undefined),
        LOCALES[DEFAULT_LOCALE]
      );
      if (typeof fallback === 'string') {
        return interpolate(fallback, params);
      }
    }
    return key;
  }
  return interpolate(value, params);
}

function interpolate(template, params) {
  if (!params || typeof params !== 'object') return template;
  return template.replace(/\{(\w+)\}/g, (_, name) =>
    Object.prototype.hasOwnProperty.call(params, name)
      ? String(params[name])
      : `{${name}}`
  );
}

export const currentLocale = computed(() => state.current);

export default {
  install(app) {
    app.config.globalProperties.$t = t;
    // Make `this.$locale` (string) work too.
    Object.defineProperty(app.config.globalProperties, '$locale', {
      get: () => state.current,
    });
    // For Composition API: inject('i18n').
    app.provide('i18n', { t, setLocale, getLocale, state });
  },
};
