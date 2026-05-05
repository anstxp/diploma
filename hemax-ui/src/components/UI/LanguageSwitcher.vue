<template>
  <div :class="['lang-switcher', `variant-${variant}`]">
    <button
      v-for="loc in locales"
      :key="loc.code"
      type="button"
      :class="['lang-btn', { active: current === loc.code }]"
      :aria-pressed="current === loc.code ? 'true' : 'false'"
      :title="loc.fullLabel"
      @click="onSwitch(loc.code)"
    >
      {{ loc.shortLabel }}
    </button>
  </div>
</template>

<script>
import { setLocale, getLocale } from "@/i18n";

export default {
  name: "LanguageSwitcher",
  props: {
    variant: {
      type: String,
      default: "compact",
      validator: (v) => ["compact", "row"].includes(v),
    },
    syncBackend: { type: Boolean, default: true },
  },
  computed: {
    current() {
      return this.$locale;
    },
    locales() {
      return [
        {
          code: "uk",
          shortLabel: this.$t("locale.ukShort"),
          fullLabel: this.$t("locale.uk"),
        },
        {
          code: "en",
          shortLabel: this.$t("locale.enShort"),
          fullLabel: this.$t("locale.en"),
        },
      ];
    },
  },
  methods: {
    onSwitch(code) {
      if (code === this.current) return;
      if (this.$store?._modules?.root?._children?.i18n) {
        this.$store.dispatch("i18n/setLocale", {
          locale: code,
          syncBackend: this.syncBackend,
        });
      } else {
        setLocale(code);
      }
    },
  },
  mounted() {
    if (!this.current) setLocale(getLocale());
  },
};
</script>

<style scoped lang="scss">
.lang-switcher {
  display: inline-flex;
  gap: 0.2rem;
  background: rgba(65, 90, 119, 0.08);
  border-radius: 0.5rem;
  padding: 0.2rem;
  user-select: none;

  &.variant-row {
    gap: 0.4rem;
    padding: 0.3rem;
    background: rgba(65, 90, 119, 0.04);
    border: 1px solid rgba(65, 90, 119, 0.12);
  }
}

.lang-btn {
  background: transparent;
  border: 0;
  padding: 0.35rem 0.8rem;
  border-radius: 0.4rem;
  font-family: inherit;
  font-size: 1.15rem;
  font-weight: 600;
  letter-spacing: 0.05rem;
  color: var(--light-color, #6b7280);
  cursor: pointer;
  text-transform: uppercase;
  transition: background 0.15s, color 0.15s;

  &:hover { color: var(--black, #111); }

  &.active {
    background: white;
    color: var(--purple, #415A77);
    box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
  }
}

.variant-row .lang-btn {
  padding: 0.5rem 1.2rem;
  font-size: 1.3rem;
}
</style>
