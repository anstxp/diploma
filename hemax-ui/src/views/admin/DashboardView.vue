<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <h1 class="page-title">{{ $t('admin.panelTitle') }}</h1>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">{{ $t('admin.stats.usersLabel') }}</div>
        <div class="stat-value">{{ counts.users || '—' }}</div>
        <div class="stat-trend">{{ $t('admin.stats.usersTrend') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ $t('admin.stats.analysesLabel') }}</div>
        <div class="stat-value">{{ counts.analyses || '—' }}</div>
        <div class="stat-trend">{{ $t('admin.stats.analysesTrend') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ $t('admin.stats.postsLabel') }}</div>
        <div class="stat-value">{{ counts.posts || '—' }}</div>
        <div class="stat-trend">{{ $t('admin.stats.postsTrend') }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">{{ $t('admin.stats.auditLabel') }}</div>
        <div class="stat-value">{{ counts.auditEvents || '—' }}</div>
        <div class="stat-trend">{{ $t('admin.stats.auditTrend') }}</div>
      </div>
    </div>

    <div class="admin-grid">
      <router-link to="/admin/users" class="action-card">
        <i class="fa-solid fa-users"></i>
        <h3>{{ $t('admin.actions.usersTitle') }}</h3>
        <p>{{ $t('admin.actions.usersDesc') }}</p>
      </router-link>
      <router-link to="/admin/audit-log" class="action-card">
        <i class="fa-solid fa-clipboard-list"></i>
        <h3>{{ $t('admin.actions.auditTitle') }}</h3>
        <p>{{ $t('admin.actions.auditDesc') }}</p>
      </router-link>
      <button class="action-card" @click="onTestEncryption">
        <i class="fa-solid fa-shield-halved"></i>
        <h3>{{ $t('admin.actions.encryptionTitle') }}</h3>
        <p>{{ $t('admin.actions.encryptionDesc') }}</p>
      </button>
    </div>

    <div v-if="encryptionResult" class="encryption-result">
      <h3>{{ $t('admin.encryptionResultTitle') }}</h3>
      <pre>{{ JSON.stringify(encryptionResult, null, 2) }}</pre>
    </div>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import { adminApi } from "@/api/users";

export default {
  name: "AdminDashboardView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent },
  data() {
    return {
      counts: {},
      encryptionResult: null,
    };
  },
  async mounted() {
    try {
      const [users, audit] = await Promise.all([
        adminApi.listUsers({ pageSize: 1 }),
        adminApi.auditLog({ pageSize: 1 }),
      ]);
      this.counts = {
        users: users.data.totalCount ?? users.data.total ?? users.data.length ?? 0,
        auditEvents: audit.data.totalCount ?? audit.data.total ?? audit.data.length ?? 0,
      };
    } catch {
      this.$store.dispatch("flash", { type: "error", message: this.$t('admin.loadStatsError') });
    }
  },
  methods: {
    async onTestEncryption() {
      try {
        const { data } = await adminApi.encryptionTest();
        this.encryptionResult = data;
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('admin.encryptionError'),
        });
      }
    },
  },
};
</script>

<style scoped lang="scss">
.admin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(24rem, 1fr));
  gap: 1.4rem;
  margin-top: 2rem;
}

.action-card {
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 2rem;
  text-align: left;
  cursor: pointer;
  font-family: inherit;
  display: block;
  transition: all 0.2s;

  &:hover {
    border-color: var(--purple);
    transform: translateY(-2px);
    box-shadow: var(--box-shadow);
  }

  i {
    width: 4.4rem;
    height: 4.4rem;
    border-radius: 0.5rem;
    background: rgba(65, 90, 119, 0.1);
    color: var(--purple);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.8rem;
    margin-bottom: 1rem;
  }

  h3 {
    font-size: 1.7rem;
    color: var(--black);
    margin-bottom: 0.4rem;
    text-transform: none;
    font-weight: 600;
  }

  p {
    font-size: 1.3rem;
    color: var(--light-color);
    text-transform: none;
  }
}

.encryption-result {
  margin-top: 2rem;
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 1.5rem;

  h3 {
    font-size: 1.4rem;
    color: var(--purple);
    text-transform: uppercase;
    letter-spacing: 0.1rem;
    font-weight: 600;
    margin-bottom: 1rem;
  }

  pre {
    background: rgba(0,0,0,0.04);
    padding: 1rem;
    border-radius: 0.4rem;
    font-size: 1.2rem;
    font-family: 'Courier New', monospace;
    overflow-x: auto;
    color: var(--black);
    white-space: pre-wrap;
    word-break: break-all;
  }
}
</style>
