<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <h1 class="page-title">{{ $t('newAnalysis.pageTitle') }}</h1>

    <div class="kind-grid" v-if="!selectedKind">
      <button
        v-for="k in kinds"
        :key="k.id"
        class="kind-tile"
        @click="selectedKind = k.id"
      >
        <i :class="k.icon"></i>
        <span class="kind-name">{{ $t(`newAnalysis.kinds.${k.id}.title`) }}</span>
        <span class="kind-desc">{{ $t(`newAnalysis.kinds.${k.id}.desc`) }}</span>
      </button>
    </div>

    <div v-else class="form-wrap">
      <div class="form-head">
        <button class="link-back" @click="selectedKind = null">
          <i class="fa-solid fa-arrow-left"></i> {{ $t('newAnalysis.backToTypes') }}
        </button>
        <h2>{{ kindTitle }}</h2>
      </div>

      <component
        :is="formComponent"
        :initial-age="userAge"
        :initial-sex="userSex"
        @submitted="onSubmitted"
      />
    </div>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import CbcForm from "@/components/analysis-components/cbc/cbc-form.vue";
import ChemForm from "@/components/analysis-components/chem/chem-form.vue";
import RiskForm from "@/components/analysis-components/risk/risk-form.vue";
import NeuroForm from "@/components/analysis-components/neuro/neuro-form.vue";
import DermaForm from "@/components/analysis-components/derma/derma-form.vue";

export default {
  name: "NewAnalysisView",
  components: {
    HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent,
    CbcForm, ChemForm, RiskForm, NeuroForm, DermaForm,
  },
  data() {
    return {
      selectedKind: null,
      kinds: [
        { id: "cbc",   icon: "fa-solid fa-droplet" },
        { id: "chem",  icon: "fa-solid fa-flask" },
        { id: "risk",  icon: "fa-solid fa-heart-pulse" },
        { id: "neuro", icon: "fa-solid fa-brain" },
        { id: "derma", icon: "fa-solid fa-camera" },
      ],
    };
  },
  computed: {
    user() { return this.$store.state.auth.user || {}; },
    userAge() {
      if (!this.user.dateOfBirth) return 30;
      const d = new Date(this.user.dateOfBirth);
      return Math.floor((Date.now() - d.getTime()) / (1000 * 60 * 60 * 24 * 365.25));
    },
    userSex() { return this.user.sex || "Unknown"; },
    formComponent() {
      const map = { cbc: "CbcForm", chem: "ChemForm", risk: "RiskForm", neuro: "NeuroForm", derma: "DermaForm" };
      return map[this.selectedKind];
    },
    kindTitle() {
      if (!this.selectedKind) return "";
      const title = this.$t(`newAnalysis.kinds.${this.selectedKind}.title`);
      const desc  = this.$t(`newAnalysis.kinds.${this.selectedKind}.desc`);
      return `${title} — ${desc}`;
    },
  },
  mounted() {
    if (this.$route.query.kind) {
      this.selectedKind = this.$route.query.kind;
    }
  },
  methods: {
    onSubmitted(result) {
      this.$router.push(`/analyses/${result.id}`);
    },
  },
};
</script>

<style scoped lang="scss">
.kind-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(22rem, 1fr));
  gap: 1.5rem;
  margin-top: 2rem;
}

.kind-tile {
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 2.4rem 2rem;
  cursor: pointer;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;
  font-family: inherit;
  transition: all 0.2s;

  &:hover {
    border-color: var(--purple);
    transform: translateY(-4px);
    box-shadow: var(--box-shadow);
  }

  i {
    width: 6rem;
    height: 6rem;
    border-radius: 50%;
    background: var(--purple);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.4rem;
    margin-bottom: 0.5rem;
  }

  .kind-name {
    font-size: 1.7rem;
    font-weight: 600;
    color: var(--black);
    text-transform: none;
  }

  .kind-desc {
    font-size: 1.2rem;
    color: var(--light-color);
    text-transform: none;
  }
}

.form-wrap { margin-top: 2rem; }

.form-head {
  margin-bottom: 1.5rem;

  .link-back {
    background: transparent;
    color: var(--purple);
    font-size: 1.3rem;
    cursor: pointer;
    margin-bottom: 1rem;
    text-transform: none;
    font-family: inherit;
    &:hover { text-decoration: underline; }
  }

  h2 {
    font-size: 2.2rem;
    color: var(--black);
    text-transform: none;
    font-weight: 500;
  }
}
</style>
