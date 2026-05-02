<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <div class="page-head">
      <h1 class="page-title">{{ $t('analyses.listTitle') }}</h1>
      <router-link to="/analyses/new" class="btn">
        <i class="fa-solid fa-plus"></i> {{ $t('analyses.newAnalysisButton') }}
      </router-link>
    </div>

    <div class="filters">
      <button
        v-for="k in kinds"
        :key="k.id"
        :class="['tab', { active: filter === k.id }]"
        @click="filter = k.id"
      >
        {{ filterLabel(k.id) }}
      </button>
    </div>

    <div v-if="loading" class="loader">{{ $t('analyses.loading') }}</div>

    <div v-else-if="filtered.length === 0" class="empty-state">
      <i class="fa-solid fa-flask"></i>
      <p>{{ $t('analyses.emptyFilter') }}</p>
      <router-link to="/analyses/new" class="btn">{{ $t('analyses.emptyCreate') }}</router-link>
    </div>

    <div v-else class="analyses-grid">
      <div
        v-for="a in filtered"
        :key="a.id"
        class="analysis-card"
        :class="{ 'has-image': isDerma(a) && a.fileUrl }"
        @click="$router.push(`/analyses/${a.id}`)"
        role="link" tabindex="0"
        @keyup.enter="$router.push(`/analyses/${a.id}`)"
      >
        <button
          class="card-delete"
          :title="$t('analyses.delete.tooltipCard')"
          @click.stop="confirmDelete(a)"
        >
          <i class="fa-solid fa-trash"></i>
        </button>

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
            {{ a.fileName || $t('analyses.pdfFallback') }}
          </p>
        </div>
        <div class="card-foot">
          <span><i class="fa-solid fa-clock"></i> {{ formatDate(a.createdAt) }}</span>
          <span v-if="a.doctorReviewedAt" class="reviewed">
            <i class="fa-solid fa-user-doctor"></i> {{ $t('analyses.reviewed') }}
          </span>
        </div>
      </div>
    </div>

    <!-- Delete confirmation modal -->
    <div v-if="toDelete" class="modal-overlay" @click.self="toDelete = null">
      <div class="modal">
        <h3><i class="fa-solid fa-triangle-exclamation"></i> {{ $t('analyses.delete.modalTitle') }}</h3>
        <p>{{ $t('analyses.delete.modalBody') }}</p>
        <p class="meta">
          <strong>{{ kindName(toDelete.type) }}</strong> · {{ formatDate(toDelete.createdAt) }}
        </p>
        <div class="modal-actions">
          <button class="btn btn-secondary" :disabled="deleting" @click="toDelete = null">
            {{ $t('analyses.delete.cancel') }}
          </button>
          <button class="btn btn-danger" :disabled="deleting" @click="doDelete">
            {{ deleting ? $t('analyses.delete.deleting') : $t('analyses.delete.confirm') }}
          </button>
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
import SeverityBadge from "@/components/analysis-components/common/SeverityBadge.vue";

const KIND_SHORT = { Cbc: "CBC", Chem: "CHEM", Risk: "RISK", Neuro: "NEURO", Derma: "DERMA" };

export default {
  name: "AnalysesView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent, SeverityBadge },
  data() {
    return {
      loading: false,
      filter: "all",
      toDelete: null,    // analysis pending confirmation
      deleting: false,
      kinds: [
        { id: "all"   },
        { id: "Cbc"   },
        { id: "Chem"  },
        { id: "Risk"  },
        { id: "Neuro" },
        { id: "Derma" },
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
    filterLabel(id) {
      const key = id === "all" ? "all" : id.toLowerCase();
      return this.$t(`analyses.filters.${key}`);
    },
    kindName(t) {
      const path = `analyses.kindNamesShort.${t}`;
      const v = this.$t(path);
      return v === path ? t : v;
    },
    shortKind(t) { return KIND_SHORT[t] || t; },
    formatDate(iso) {
      const lang = this.$locale === "en" ? "en-US" : "uk-UA";
      return new Date(iso).toLocaleDateString(lang, {
        day: "numeric", month: "short", year: "numeric",
      });
    },
    summary(a) {
      return a.summaryUa || a.result?.summary || this.$t('analyses.defaultSummary');
    },
    isDerma(a) {
      const t = String(a.type).toLowerCase();
      return t === "derma" || a.type === 5 || t === "5";
    },
    onImgError(ev) {
      ev.target.style.display = "none";
      const card = ev.target.closest(".analysis-card");
      if (card) card.classList.remove("has-image");
    },

    confirmDelete(a) {
      this.toDelete = a;
    },

    async doDelete() {
      if (!this.toDelete) return;
      this.deleting = true;
      try {
        await this.$store.dispatch("analyses/remove", this.toDelete.id);
        const idx = this.$store.state.analyses.list.findIndex(x => x.id === this.toDelete.id);
        if (idx !== -1) this.$store.state.analyses.list.splice(idx, 1);
        this.toDelete = null;
      } catch (err) {
        console.error("Failed to delete analysis", err);
        alert(this.$t('analyses.delete.errorAlert'));
      } finally {
        this.deleting = false;
      }
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

  .btn { display: inline-flex; align-items: center; gap: 0.5rem; }
}

.filters { margin-bottom: 2rem; }

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

  &.has-image { padding-top: 0; }

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

  &:hover .card-thumb img { transform: scale(1.05); }

  .attachment {
    margin-top: 0.6rem;
    font-size: 1.2rem;
    color: var(--light-color);
    text-transform: none;
    display: flex;
    align-items: center;
    gap: 0.5rem;

    i { color: #C5380F; font-size: 1.4rem; }
  }

  .card-head { display: flex; justify-content: space-between; align-items: center; }

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

    .flag { color: #A32D2D; font-weight: 500; }
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

/* Delete button on each card */
.analysis-card {
  position: relative;
  cursor: pointer;

  .card-delete {
    position: absolute;
    top: 0.8rem;
    right: 0.8rem;
    width: 3.2rem;
    height: 3.2rem;
    border: none;
    background: rgba(255, 255, 255, 0.92);
    color: #A32D2D;
    border-radius: 50%;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    opacity: 0;
    transition: opacity 0.15s ease, transform 0.15s ease;
    z-index: 2;
    box-shadow: 0 2px 6px rgba(0,0,0,0.1);

    &:hover { background: #A32D2D; color: #fff; transform: scale(1.08); }
  }
  &:hover .card-delete,
  &:focus-within .card-delete { opacity: 1; }
}

/* Confirmation modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;

  .modal {
    background: #fff;
    border-radius: 12px;
    padding: 2.5rem;
    max-width: 480px;
    width: 100%;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);

    h3 {
      font-size: 1.8rem;
      color: #A32D2D;
      margin-bottom: 1.2rem;
      display: flex;
      align-items: center;
      gap: 0.7rem;

      i { color: #f59e0b; }
    }

    p {
      font-size: 1.4rem;
      color: var(--black);
      line-height: 1.55;
      margin-bottom: 1rem;
      text-transform: none;

      &.meta {
        font-size: 1.3rem;
        color: var(--light-color);
        background: #f5f5f5;
        padding: 0.8rem 1.2rem;
        border-radius: 6px;
      }
    }

    .modal-actions {
      display: flex;
      gap: 1rem;
      justify-content: flex-end;
      margin-top: 2rem;

      .btn-secondary {
        background: transparent;
        color: var(--black);
        border: 1px solid #ccc;
      }
      .btn-danger {
        background: #A32D2D;
        color: #fff;
        border: 1px solid #A32D2D;

        &:disabled { opacity: 0.6; cursor: not-allowed; }
      }
    }
  }
}
</style>
