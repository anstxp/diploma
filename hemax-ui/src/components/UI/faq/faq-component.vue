<template>
  <section class="faq">
    <div class="heading"><span>{{ $t('faq.heading') }}</span></div>

    <div class="faq-list">
      <div
        v-for="(item, i) in items"
        :key="item.key"
        :class="['faq-item', { open: openIdx === i }]"
        @click="toggle(i)"
      >
        <div class="q">
          <span>{{ $t(`faq.items.${item.key}.q`) }}</span>
          <i :class="openIdx === i ? 'fa-solid fa-minus' : 'fa-solid fa-plus'"></i>
        </div>
        <div class="a" v-show="openIdx === i">{{ $t(`faq.items.${item.key}.a`) }}</div>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: "FaqComponent",
  data() {
    return {
      openIdx: 0,
      items: [
        { key: "security" },
        { key: "models" },
        { key: "doctor" },
        { key: "invite" },
        { key: "export" },
      ],
    };
  },
  methods: {
    toggle(i) {
      this.openIdx = this.openIdx === i ? -1 : i;
    },
  },
};
</script>

<style scoped lang="scss">
.faq {
  padding: 4rem 9%;

  .faq-list {
    max-width: 80rem;
    margin: 0 auto;
  }

  .faq-item {
    background: white;
    border: var(--border);
    border-radius: .6rem;
    margin-bottom: 1rem;
    cursor: pointer;
    overflow: hidden;

    &.open { border-color: var(--purple); }

    .q {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 1.4rem 1.8rem;
      font-size: 1.5rem;
      color: var(--black);
      font-weight: 500;
      text-transform: none;

      i { color: var(--purple); font-size: 1.4rem; }
    }

    .a {
      padding: 0 1.8rem 1.4rem;
      font-size: 1.3rem;
      color: var(--light-color);
      line-height: 1.8;
      text-transform: none;
      border-top: var(--border);
      padding-top: 1.4rem;
    }
  }
}

@media (max-width: 768px) {
  .faq { padding: 3rem 5%; }
}
</style>
