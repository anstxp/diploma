<template>
  <section class="hero">
    <div class="row">
      <div class="content">
        <h3>{{ $t('landing.hero.titleLine1') }}<br />{{ $t('landing.hero.titleLine2') }}</h3>
        <p>{{ $t('landing.hero.body') }}</p>
        <router-link
          :to="isAuth ? '/analyses/new' : '/sign-up'"
          class="btn"
        >{{ isAuth ? $t('landing.hero.ctaAuth') : $t('landing.hero.ctaGuest') }}</router-link>
      </div>

      <div class="modules">
        <div class="module-tile" v-for="m in modules" :key="m.kind">
          <div class="icon" :style="{ background: m.color }">
            <i :class="m.icon"></i>
          </div>
          <div class="tile-text">
            <span class="tile-title">{{ $t(`landing.hero.modules.${m.kind}.title`) }}</span>
            <span class="tile-sub">{{ $t(`landing.hero.modules.${m.kind}.subtitle`) }}</span>
          </div>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
export default {
  name: "HeroComponent",
  computed: {
    isAuth() { return this.$store.state.auth.isAuth; },
  },
  data() {
    return {
      modules: [
        { kind: 'cbc',   icon: 'fa-solid fa-droplet',      color: '#415A77' },
        { kind: 'chem',  icon: 'fa-solid fa-flask',        color: '#1B263B' },
        { kind: 'risk',  icon: 'fa-solid fa-heart-pulse',  color: '#415A77' },
        { kind: 'neuro', icon: 'fa-solid fa-brain',        color: '#1B263B' },
        { kind: 'derma', icon: 'fa-solid fa-camera',       color: '#415A77' },
      ],
    };
  },
};
</script>

<style scoped lang="scss">
.hero {
  padding: 6rem 9% 4rem;
  background: linear-gradient(180deg, white 0%, var(--bg) 100%);

  .row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 4rem;
  }

  .content {
    flex: 1 1 40rem;

    h3 {
      font-size: 4.5rem;
      color: var(--black);
      line-height: 1.2;
      margin-bottom: 1.5rem;
      font-weight: 600;
      text-transform: none;
    }

    p {
      font-size: 1.5rem;
      line-height: 1.8;
      color: var(--light-color);
      text-transform: none;
      margin-bottom: 1rem;
    }
  }

  .modules {
    flex: 1 1 36rem;
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 1.4rem;
  }

  .module-tile {
    background: white;
    border: var(--border);
    border-radius: .8rem;
    padding: 1.4rem;
    display: flex;
    align-items: center;
    gap: 1.2rem;
    cursor: pointer;
    transition: transform 0.15s;

    &:hover { transform: translateY(-2px); border-color: var(--purple); }

    .icon {
      width: 4.4rem;
      height: 4.4rem;
      border-radius: .6rem;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 1.8rem;
      flex-shrink: 0;
    }

    .tile-text { display: flex; flex-direction: column; }
    .tile-title { font-size: 1.5rem; color: var(--black); font-weight: 600; }
    .tile-sub { font-size: 1.2rem; color: var(--light-color); text-transform: none; }
  }
}

@media (max-width: 768px) {
  .hero {
    padding: 4rem 5% 3rem;
    .content h3 { font-size: 3.2rem; }
    .modules { grid-template-columns: 1fr; }
  }
}
</style>
