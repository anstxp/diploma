<template>
  <section class="features">
    <div class="heading"><span>{{ $t('landing.features.heading') }}</span></div>

    <div class="features-grid">
      <div class="feature" v-for="f in features" :key="f.key">
        <div class="feature-icon">
          <i :class="f.icon"></i>
        </div>
        <h4>{{ $t(`landing.features.${f.key}.title`) }}</h4>
        <p>{{ $t(`landing.features.${f.key}.text`) }}</p>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: "FeaturesComponent",
  data() {
    return {
      features: [
        { key: 'encryption', icon: 'fa-solid fa-shield-halved' },
        { key: 'speed',      icon: 'fa-solid fa-bolt' },
        { key: 'doctors',    icon: 'fa-solid fa-user-doctor' },
        { key: 'dynamics',   icon: 'fa-solid fa-chart-line' },
        { key: 'language',   icon: 'fa-solid fa-language' },
        { key: 'mobile',     icon: 'fa-solid fa-mobile-screen' },
      ],
    };
  },
};
</script>

<style scoped lang="scss">
.features {
  padding: 4rem 9%;

  .features-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(28rem, 1fr));
    gap: 2rem;
  }

  .feature {
    background: white;
    border: var(--border);
    border-radius: .8rem;
    padding: 2.4rem 2rem;
    text-align: center;
    transition: transform 0.15s;

    &:hover {
      transform: translateY(-4px);
      box-shadow: var(--box-shadow);
      border-color: var(--purple);
    }

    .feature-icon {
      width: 5.6rem;
      height: 5.6rem;
      border-radius: 50%;
      background: var(--purple);
      color: white;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      font-size: 2.2rem;
      margin-bottom: 1.2rem;
    }

    h4 {
      font-size: 1.7rem;
      color: var(--black);
      margin-bottom: 0.8rem;
      font-weight: 600;
    }

    p {
      font-size: 1.3rem;
      color: var(--light-color);
      line-height: 1.7;
      text-transform: none;
    }
  }
}

@media (max-width: 768px) {
  .features { padding: 3rem 5%; }
}
</style>
