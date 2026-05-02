<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page user-home">
    <div class="welcome">
      <div>
        <h1 class="page-title">{{ $t('userHome.greetingPrefix') }}, {{ user.firstName }} 👋</h1>
        <p class="subtitle">{{ today }}</p>
      </div>
      <button class="btn-outline btn-small" @click="logout">
        <i class="fa-solid fa-right-from-bracket"></i> {{ $t('userHome.logout') }}
      </button>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">{{ $t('userHome.totalLabel') }}</div>
        <div class="stat-value">{{ stats.total }}</div>
        <div class="stat-trend">{{ stats.thisMonth }} {{ $t('userHome.thisMonthSuffix') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ $t('userHome.flaggedLabel') }}</div>
        <div class="stat-value">{{ stats.flagged }}</div>
        <div class="stat-trend">{{ $t('userHome.flaggedTrend') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ $t('userHome.reviewedLabel') }}</div>
        <div class="stat-value">{{ stats.reviewed }}</div>
        <div class="stat-trend">{{ $t('userHome.reviewedTrend') }}</div>
      </div>
    </div>

    <div class="quick-actions">
      <router-link to="/analyses/new" class="action">
        <i class="fa-solid fa-plus"></i>
        <span>{{ $t('userHome.actionNewAnalysis') }}</span>
      </router-link>
      <router-link to="/analyses" class="action">
        <i class="fa-solid fa-clock-rotate-left"></i>
        <span>{{ $t('userHome.actionHistory') }}</span>
      </router-link>
      <router-link to="/update-profile" class="action">
        <i class="fa-solid fa-user-pen"></i>
        <span>{{ $t('userHome.actionEditProfile') }}</span>
      </router-link>
      <router-link v-if="isDoctor" to="/patients" class="action">
        <i class="fa-solid fa-users"></i>
        <span>{{ $t('userHome.actionMyPatients') }}</span>
      </router-link>
    </div>

    <section class="recent">
      <div class="heading"><span>{{ $t('userHome.recentTitle') }}</span></div>

      <div v-if="loading" class="loader">{{ $t('userHome.loading') }}</div>
      <div v-else-if="recent.length === 0" class="empty-state">
        <i class="fa-solid fa-flask"></i>
        <p>{{ $t('userHome.emptyText') }}</p>
        <router-link to="/analyses/new" class="btn">{{ $t('userHome.createFirstButton') }}</router-link>
      </div>
      <div v-else class="analyses-list">
        <router-link
          v-for="a in recent"
          :key="a.id"
          :to="`/analyses/${a.id}`"
          class="analysis-row"
        >
          <div class="kind-badge" :title="a.type">{{ shortKind(a.type) }}</div>
          <div class="row-body">
            <div class="row-title">{{ kindName(a.type) }}</div>
            <div class="row-meta">{{ formatDate(a.createdAt) }}</div>
          </div>
          <SeverityBadge :severity="a.severityLabel || a.severity" />
        </router-link>
        <router-link to="/analyses" class="view-all">{{ $t('userHome.viewAll') }}</router-link>
      </div>
    </section>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import SeverityBadge from "@/components/analysis-components/common/SeverityBadge.vue";
import { normalizeKindCode } from "@/constants/analysisConstants";

const KIND_SHORT = { Cbc: "CBC", Chem: "CHEM", Risk: "RISK", Neuro: "NEURO", Derma: "DERMA" };

export default {
  name: "UserHome",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent, SeverityBadge },
  data() {
    return { loading: false };
  },
  computed: {
    user() { return this.$store.state.auth.user || {}; },
    isDoctor() { return this.$store.getters["auth/isDoctor"]; },
    recent() { return this.$store.state.analyses.list.slice(0, 5); },
    stats() {
      const list = this.$store.state.analyses.list;
      const total = this.$store.state.analyses.total || list.length;
      const thisMonthStart = new Date();
      thisMonthStart.setDate(1);
      thisMonthStart.setHours(0, 0, 0, 0);
      return {
        total,
        thisMonth: list.filter((a) => new Date(a.createdAt) >= thisMonthStart).length,
        flagged: list.filter((a) => {
          const s = String(a.severityLabel || a.severity || "").toLowerCase();
          return ["mild", "moderate", "monitor", "warning", "severe", "urgent", "critical", "2", "3", "4"].includes(s);
        }).length,
        reviewed: list.filter((a) => a.doctorNote || a.doctorReviewedAt || a.hasDoctorReview).length,
      };
    },
    today() {
      const lang = this.$locale === "en" ? "en-US" : "uk-UA";
      return new Date().toLocaleDateString(lang, {
        weekday: "long", day: "numeric", month: "long",
      });
    },
  },
  async mounted() {
    this.loading = true;
    try {
      await this.$store.dispatch("analyses/loadMy", { pageSize: 50 });
    } finally {
      this.loading = false;
    }
  },
  methods: {
    kindName(t) {
      const path = `analyses.kindNamesShort.${t}`;
      const v = this.$t(path);
      return v === path ? t : v;
    },
    shortKind(t) { return KIND_SHORT[t] || t; },
    _kindCode(t) { return normalizeKindCode(t); },
    formatDate(iso) {
      const lang = this.$locale === "en" ? "en-US" : "uk-UA";
      return new Date(iso).toLocaleString(lang, { dateStyle: "short", timeStyle: "short" });
    },
    async logout() {
      await this.$store.dispatch("auth/logout");
      this.$router.push("/");
    },
  },
};
</script>

<style scoped lang="scss">
.user-home .welcome {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 2rem;

  .subtitle {
    font-size: 1.4rem;
    color: var(--light-color);
    text-transform: none;
  }

  .btn-outline {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
  }
}

.quick-actions {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr));
  gap: 1.4rem;
  margin: 2rem 0 3rem;

  .action {
    background: white;
    border: var(--border);
    border-radius: 0.6rem;
    padding: 1.6rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    transition: all 0.2s;

    &:hover {
      border-color: var(--purple);
      transform: translateY(-2px);
    }

    i {
      width: 4rem;
      height: 4rem;
      border-radius: 0.5rem;
      background: rgba(65, 90, 119, 0.1);
      color: var(--purple);
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 1.6rem;
    }

    span {
      font-size: 1.4rem;
      color: var(--black);
      text-transform: none;
      font-weight: 500;
    }
  }
}

.recent { margin-top: 3rem; }

.analyses-list {
  display: flex;
  flex-direction: column;
  gap: 0;
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  overflow: hidden;
}

.analysis-row {
  display: grid;
  grid-template-columns: 5rem 1fr auto;
  gap: 1.2rem;
  align-items: center;
  padding: 1.2rem 1.6rem;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  transition: background 0.15s;

  &:last-of-type { border-bottom: none; }
  &:hover { background: rgba(65, 90, 119, 0.04); }

  .kind-badge {
    width: 4.4rem;
    height: 4.4rem;
    border-radius: 50%;
    background: var(--purple);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    font-weight: 600;
  }

  .row-title {
    font-size: 1.4rem;
    color: var(--black);
    font-weight: 500;
    margin-bottom: 0.2rem;
    text-transform: none;
  }

  .row-meta {
    font-size: 1.2rem;
    color: var(--light-color);
    text-transform: none;
  }
}

.view-all {
  display: block;
  text-align: right;
  padding: 1.2rem 1.6rem;
  color: var(--purple);
  font-size: 1.3rem;
  text-decoration: underline;
  text-transform: lowercase;
  background: rgba(65, 90, 119, 0.04);

  &:hover { background: rgba(65, 90, 119, 0.08); }
}
</style>
