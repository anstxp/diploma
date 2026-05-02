<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <h1 class="page-title">{{ $t('admin.auditPage.pageTitle') }}</h1>

    <div class="admin-toolbar">
      <div class="filter-group">
        <label>{{ $t('admin.auditPage.fromDate') }}</label>
        <input v-model="filters.fromUtc" type="date" class="box" @change="load" />
      </div>
      <div class="filter-group">
        <label>{{ $t('admin.auditPage.toDate') }}</label>
        <input v-model="filters.toUtc" type="date" class="box" @change="load" />
      </div>
      <div class="filter-group">
        <label>{{ $t('admin.auditPage.actionFilter') }}</label>
        <input
          v-model="filters.action"
          type="text"
          class="box"
          :placeholder="$t('admin.auditPage.actionPlaceholder')"
          @input="debouncedLoad"
        />
      </div>
      <button class="btn-outline btn-small" @click="resetFilters">{{ $t('admin.auditPage.resetButton') }}</button>
    </div>

    <div v-if="loading" class="loader">{{ $t('admin.auditPage.loading') }}</div>

    <div v-else-if="events.length === 0" class="empty-state">
      <i class="fa-solid fa-clipboard-list"></i>
      <p>{{ $t('admin.auditPage.emptyText') }}</p>
    </div>

    <div v-else class="audit-wrap">
      <table class="table">
        <thead>
          <tr>
            <th>{{ $t('admin.auditPage.tableTime') }}</th>
            <th>{{ $t('admin.auditPage.tableUser') }}</th>
            <th>{{ $t('admin.auditPage.tableAction') }}</th>
            <th>{{ $t('admin.auditPage.tableEntity') }}</th>
            <th>{{ $t('admin.auditPage.tableIp') }}</th>
            <th>{{ $t('admin.auditPage.tableDetails') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="e in events" :key="e.id">
            <td class="time">{{ formatDate(e.timestamp || e.createdAt) }}</td>
            <td>
              <div class="user-cell">
                <span class="email">{{ e.userEmail || e.userId || "—" }}</span>
              </div>
            </td>
            <td><span class="action-pill">{{ e.actionName || e.action }}</span></td>
            <td class="entity">
              <span v-if="e.entityType">{{ e.entityType }}</span>
              <span v-if="e.entityId" class="entity-id">{{ shortId(e.entityId) }}</span>
            </td>
            <td class="ip">{{ e.ipAddress || "—" }}</td>
            <td>
              <button v-if="e.detailsJson || e.details" class="link-action" @click="showDetails(e)">
                {{ $t('admin.auditPage.viewDetails') }}
              </button>
              <span v-else class="muted">—</span>
            </td>
          </tr>
        </tbody>
      </table>

      <div v-if="hasMore" class="load-more">
        <button class="btn-outline btn-small" @click="loadMore" :disabled="loadingMore">
          {{ loadingMore ? $t('admin.auditPage.loadMoreLoading') : $t('admin.auditPage.loadMore') }}
        </button>
      </div>
    </div>

    <div v-if="modalEvent" class="modal-overlay" @click.self="modalEvent = null">
      <div class="modal">
        <div class="modal-head">
          <h3>{{ $t('admin.auditPage.modalTitle') }}</h3>
          <button class="close" @click="modalEvent = null">
            <i class="fa-solid fa-xmark"></i>
          </button>
        </div>
        <div class="modal-body">
          <div class="kv"><span>{{ $t('admin.auditPage.kvAction') }}</span><strong>{{ modalEvent.actionName || modalEvent.action }}</strong></div>
          <div class="kv"><span>{{ $t('admin.auditPage.kvTime') }}</span><strong>{{ formatDate(modalEvent.timestamp || modalEvent.createdAt) }}</strong></div>
          <div class="kv" v-if="modalEvent.userEmail || modalEvent.userId">
            <span>{{ $t('admin.auditPage.kvUser') }}</span><strong>{{ modalEvent.userEmail || modalEvent.userId }}</strong>
          </div>
          <div class="kv" v-if="modalEvent.entityType">
            <span>{{ $t('admin.auditPage.kvEntity') }}</span><strong>{{ modalEvent.entityType }} {{ modalEvent.entityId }}</strong>
          </div>
          <div class="kv" v-if="modalEvent.ipAddress">
            <span>{{ $t('admin.auditPage.kvIp') }}</span><strong>{{ modalEvent.ipAddress }}</strong>
          </div>
          <div class="kv" v-if="modalEvent.userAgent">
            <span>{{ $t('admin.auditPage.kvUserAgent') }}</span><strong class="ua">{{ modalEvent.userAgent }}</strong>
          </div>
          <div class="details-block" v-if="modalEvent.detailsJson || modalEvent.details">
            <span>{{ $t('admin.auditPage.kvPayload') }}</span>
            <pre>{{ formatDetails(modalEvent.detailsJson || modalEvent.details) }}</pre>
          </div>
        </div>
      </div>
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
  name: "AdminAuditLogView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent },
  data() {
    return {
      loading: false,
      loadingMore: false,
      events: [],
      total: 0,
      page: 1,
      pageSize: 30,
      filters: { fromUtc: "", toUtc: "", action: "" },
      modalEvent: null,
      searchTimer: null,
    };
  },
  computed: {
    hasMore() { return this.events.length < this.total; },
  },
  mounted() { this.load(); },
  methods: {
    debouncedLoad() {
      clearTimeout(this.searchTimer);
      this.searchTimer = setTimeout(this.load, 350);
    },
    buildParams() {
      const params = { page: this.page, pageSize: this.pageSize };
      if (this.filters.fromUtc) params.fromUtc = new Date(this.filters.fromUtc).toISOString();
      if (this.filters.toUtc) {
        const d = new Date(this.filters.toUtc);
        d.setHours(23, 59, 59);
        params.toUtc = d.toISOString();
      }
      if (this.filters.action) params.action = this.filters.action;
      return params;
    },
    async load() {
      this.loading = true;
      this.page = 1;
      try {
        const { data } = await adminApi.auditLog(this.buildParams());
        this.events = data.items || data || [];
        this.total = data.totalCount ?? data.total ?? this.events.length;
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('admin.auditPage.loadError'),
        });
      } finally {
        this.loading = false;
      }
    },
    async loadMore() {
      this.loadingMore = true;
      this.page += 1;
      try {
        const { data } = await adminApi.auditLog(this.buildParams());
        this.events = [...this.events, ...(data.items || data || [])];
        this.total = data.totalCount ?? data.total ?? this.events.length;
      } catch {
        this.page -= 1;
        this.$store.dispatch("flash", { type: "error", message: this.$t('admin.auditPage.errorGeneric') });
      } finally {
        this.loadingMore = false;
      }
    },
    resetFilters() {
      this.filters = { fromUtc: "", toUtc: "", action: "" };
      this.load();
    },
    showDetails(e) { this.modalEvent = e; },
    formatDate(iso) {
      if (!iso) return "—";
      const lang = this.$locale === "en" ? "en-US" : "uk-UA";
      return new Date(iso).toLocaleString(lang, { dateStyle: "short", timeStyle: "medium" });
    },
    shortId(id) {
      if (!id) return "";
      const s = String(id);
      return s.length > 12 ? s.slice(0, 8) + "…" : s;
    },
    formatDetails(d) {
      if (typeof d === "string") {
        try { return JSON.stringify(JSON.parse(d), null, 2); } catch { return d; }
      }
      return JSON.stringify(d, null, 2);
    },
  },
};
</script>

<style scoped lang="scss">
.admin-toolbar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
  align-items: flex-end;
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 1.2rem 1.4rem;

  .filter-group {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;

    label {
      font-size: 1.1rem;
      color: var(--light-color);
      text-transform: uppercase;
      letter-spacing: 0.05rem;
    }

    .box {
      padding: 0.7rem 1rem;
      font-size: 1.3rem;
      border: var(--border);
      border-radius: 0.4rem;
      text-transform: none;
      background: white;
      min-width: 16rem;

      &:focus { border-color: var(--purple); }
    }
  }
}

.audit-wrap .table {
  font-size: 1.2rem;

  td.time, td.ip {
    color: var(--light-color);
    text-transform: none;
    font-family: 'Courier New', monospace;
    font-size: 1.15rem;
    white-space: nowrap;
  }

  td.entity .entity-id {
    display: block;
    font-size: 1rem;
    color: var(--light-color);
    font-family: 'Courier New', monospace;
  }

  .user-cell .email { color: var(--black); text-transform: none; }

  .action-pill {
    display: inline-block;
    background: rgba(65, 90, 119, 0.1);
    color: var(--purple);
    padding: 0.2rem 0.7rem;
    border-radius: 0.3rem;
    font-size: 1.1rem;
    text-transform: none;
    font-weight: 500;
  }

  .muted { color: var(--light-color); }
}

.link-action {
  background: transparent;
  color: var(--purple);
  font-size: 1.2rem;
  cursor: pointer;
  font-family: inherit;
  text-transform: lowercase;

  &:hover { text-decoration: underline; }
}

.load-more { text-align: center; margin-top: 2rem; }

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(13, 27, 42, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 5000;
  padding: 2rem;
}

.modal {
  background: white;
  border-radius: 0.6rem;
  width: 100%;
  max-width: 60rem;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 1rem 3rem rgba(0,0,0,0.3);
}

.modal-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.2rem 1.5rem;
  border-bottom: var(--border);

  h3 {
    font-size: 1.6rem;
    color: var(--black);
    text-transform: uppercase;
    letter-spacing: 0.1rem;
    font-weight: 500;
  }

  .close {
    background: transparent;
    cursor: pointer;
    font-size: 1.6rem;
    color: var(--light-color);
    &:hover { color: var(--black); }
  }
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;

  .kv {
    display: grid;
    grid-template-columns: 12rem 1fr;
    gap: 1rem;
    padding: 0.7rem 0;
    border-bottom: 1px solid rgba(0,0,0,0.06);
    font-size: 1.3rem;

    span { color: var(--light-color); text-transform: lowercase; }
    strong {
      color: var(--black);
      text-transform: none;
      word-break: break-all;
      &.ua { font-size: 1.2rem; font-family: 'Courier New', monospace; }
    }
  }

  .details-block {
    margin-top: 1rem;

    span {
      display: block;
      font-size: 1.2rem;
      color: var(--light-color);
      text-transform: lowercase;
      margin-bottom: 0.5rem;
    }

    pre {
      background: rgba(0,0,0,0.04);
      padding: 1rem;
      border-radius: 0.4rem;
      font-size: 1.1rem;
      font-family: 'Courier New', monospace;
      overflow-x: auto;
      max-height: 30rem;
      color: var(--black);
      white-space: pre-wrap;
      word-break: break-all;
    }
  }
}

@media (max-width: 768px) {
  .admin-toolbar {
    flex-direction: column;
    align-items: stretch;

    .filter-group {
      width: 100%;
      .box { min-width: 0; width: 100%; }
    }
  }

  .modal-body .kv {
    grid-template-columns: 1fr;
    gap: 0.3rem;
  }
}
</style>
