<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <div class="page-head">
      <h1 class="page-title">мої аналізи</h1>
      <router-link to="/analyses/new" class="btn">
        <i class="fa-solid fa-plus"></i> новий аналіз
      </router-link>
    </div>

    <div class="filters">
      <button
        v-for="k in kinds"
        :key="k.id"
        :class="['tab', { active: filter === k.id }]"
        @click="filter = k.id"
      >
        {{ k.label }}
      </button>
    </div>

    <div v-if="loading" class="loader">завантажуємо</div>

    <div v-else-if="filtered.length === 0" class="empty-state">
      <i class="fa-solid fa-flask"></i>
      <p>немає аналізів за цим фільтром</p>
      <router-link to="/analyses/new" class="btn">створити аналіз</router-link>
    </div>

    <div v-else class="analyses-grid">
      <router-link
        v-for="a in filtered"
        :key="a.id"
        :to="`/analyses/${a.id}`"
        class="analysis-card"
        :class="{ 'has-image': isDerma(a) && a.fileUrl }"
      >
        <!-- DERMA thumbnail (lesion image) -->
        <div v-if="isDerma(a) && a.fileUrl" class="card-thumb">
          <img :src="a.fileUrl" :alt="kindName(a.type)" loading="lazy" @error="onImgError($event, a)" />
        </div>

        <div class="card-head">
          <span class="kind">{{ shortKind(a.type) }}</span>
          <SeverityBadge :severity="a.severityLabel || a.severity" />
        </div>
        <div class="card-body">
          <h3>{{ kindName(a.type) }}</h3>
          <p v-if="a.topFlag" class="flag">⚑ {{ a.topFlag }}</p>
          <p v-else class="meta">{{ summary(a) }}</p>

          <!-- PDF attachment indicator for CBC/CHEM -->
          <p v-if="a.fileUrl && !isDerma(a)" class="attachment">
            <i class="fa-solid fa-file-pdf"></i>
            {{ a.fileName || "PDF звіт" }}
          </p>
        </div>
        <div class="card-foot">
          <span><i class="fa-solid fa-clock"></i> {{ formatDate(a.createdAt) }}</span>
          <span v-if="a.doctorReviewedAt" class="reviewed">
            <i class="fa-solid fa-user-doctor"></i> переглянуто
          </span>
        </div>
      </router-link>
    </div>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import SeverityBadge from "@/components/analysis-components/common/SeverityBadge.vue";

const KIND_NAMES = { Cbc: "Загальний аналіз крові", Chem: "Біохімія", Risk: "Хронічні ризики", Neuro: "Психо скринінг", Derma: "Дерматологія" };
const KIND_SHORT = { Cbc: "CBC", Chem: "CHEM", Risk: "RISK", Neuro: "NEURO", Derma: "DERMA" };

export default {
  name: "AnalysesView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent, SeverityBadge },
  data() {
    return {
      loading: false,
      filter: "all",
      kinds: [
        { id: "all", label: "усі" },
        { id: "Cbc", label: "CBC" },
        { id: "Chem", label: "Біохімія" },
        { id: "Risk", label: "Ризики" },
        { id: "Neuro", label: "Психо" },
        { id: "Derma", label: "Дерма" },
      ],
    };
  },
  computed: {
    list() { return this.$store.state.analyses.list; },
    isDoctor() { return this.$store.getters["auth/isDoctor"]; },
    filtered() {
      if (this.filter === "all") return this.list;
      return this.list.filter((a) => a.type === this.filter);
    },
  },
  async mounted() {
    this.loading = true;
    try {
      const action = this.isDoctor && this.$route.query.patientId ? "analyses/loadAll" : "analyses/loadMy";
      const params = this.$route.query.patientId ? { patientId: this.$route.query.patientId } : { pageSize: 100 };
      await this.$store.dispatch(action, params);
    } finally {
      this.loading = false;
    }
  },
  methods: {
    kindName(t) { return KIND_NAMES[t] || t; },
    shortKind(t) { return KIND_SHORT[t] || t; },
    formatDate(iso) {
      return new Date(iso).toLocaleDateString("uk-UA", { day: "numeric", month: "short", year: "numeric" });
    },
    summary(a) {
      return a.summaryUa || a.result?.summary || "результат готовий";
    },
    /** True if analysis is DERMA (type code 5 or "Derma" string). */
    isDerma(a) {
      const t = String(a.type).toLowerCase();
      return t === "derma" || a.type === 5 || t === "5";
    },
    /** If image fails to load (expired SAS token, broken link), hide thumbnail. */
    onImgError(ev) {
      ev.target.style.display = "none";
      const card = ev.target.closest(".analysis-card");
      if (card) card.classList.remove("has-image");
    },
  },
};
</script>

<style scoped lang="scss">
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }
}

.filters {
  margin-bottom: 2rem;
}

.analyses-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(28rem, 1fr));
  gap: 1.4rem;
}

.analysis-card {
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 1.6rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  transition: all 0.2s;
  overflow: hidden;

  &:hover {
    border-color: var(--purple);
    transform: translateY(-2px);
    box-shadow: var(--box-shadow);
  }

  &.has-image {
    padding-top: 0;
  }

  .card-thumb {
    margin: -1.6rem -1.6rem 0;
    height: 14rem;
    overflow: hidden;
    background: linear-gradient(135deg, #f5f5f5, #e8e8e8);
    border-bottom: var(--border);

    img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      transition: transform 0.3s;
    }
  }

  &:hover .card-thumb img {
    transform: scale(1.05);
  }

  .attachment {
    margin-top: 0.6rem;
    font-size: 1.2rem;
    color: var(--light-color);
    text-transform: none;
    display: flex;
    align-items: center;
    gap: 0.5rem;

    i {
      color: #C5380F;
      font-size: 1.4rem;
    }
  }

  .card-head {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .kind {
    font-size: 1.2rem;
    font-weight: 600;
    color: var(--purple);
    text-transform: uppercase;
    letter-spacing: 0.1rem;
  }

  .card-body {
    h3 {
      font-size: 1.5rem;
      color: var(--black);
      font-weight: 600;
      margin-bottom: 0.4rem;
      text-transform: none;
    }

    p {
      font-size: 1.3rem;
      color: var(--light-color);
      text-transform: none;
      line-height: 1.5;
    }

    .flag {
      color: #A32D2D;
      font-weight: 500;
    }
  }

  .card-foot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 1.1rem;
    color: var(--light-color);
    padding-top: 0.8rem;
    border-top: 1px solid rgba(0,0,0,0.06);
    text-transform: none;

    i { color: var(--purple); margin-right: 0.3rem; }

    .reviewed { color: var(--purple); }
  }
}
</style>
