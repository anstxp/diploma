<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <div class="page-toolbar">
      <button class="link-back" @click="$router.back()">
        <i class="fa-solid fa-arrow-left"></i> назад
      </button>

      <div v-if="current" class="toolbar-actions">
        <a
          v-if="current.fileUrl && !isDerma"
          :href="current.fileUrl"
          target="_blank"
          rel="noopener"
          class="btn btn-secondary"
          :title="current.fileName || 'PDF звіт'"
        >
          <i class="fa-solid fa-file-pdf"></i>
          відкрити PDF
        </a>

        <button
          v-if="isOwner"
          class="btn btn-danger-ghost"
          @click="showDeleteModal = true"
          :title="'видалити цей аналіз'"
        >
          <i class="fa-solid fa-trash"></i>
          видалити
        </button>
      </div>
    </div>

    <div v-if="loading" class="loader">завантажуємо аналіз</div>

    <div v-else-if="!current" class="empty-state">
      <i class="fa-solid fa-circle-exclamation"></i>
      <p>аналіз не знайдено</p>
    </div>

    <template v-else>
      <AnalysisResult :analysis="current" />

      <div v-if="canReview" class="doctor-form">
        <h3>додати коментар лікаря</h3>
        <textarea
          v-model="note"
          rows="4"
          class="box"
          placeholder="ваш коментар та рекомендації…"
        ></textarea>
        <button class="btn" :disabled="!note.trim() || sending" @click="onReview">
          {{ sending ? "відправляємо…" : "залишити коментар" }}
        </button>
      </div>
    </template>

    <!-- Delete confirmation modal -->
    <div v-if="showDeleteModal" class="modal-overlay" @click.self="showDeleteModal = false">
      <div class="modal">
        <h3><i class="fa-solid fa-triangle-exclamation"></i> Видалити аналіз?</h3>
        <p>
          Цей аналіз буде <strong>безповоротно видалено</strong> разом з PDF
          (якщо є) і результатом інтерпретації. Цю дію не можна скасувати.
        </p>
        <div class="modal-actions">
          <button class="btn btn-secondary" :disabled="deleting" @click="showDeleteModal = false">Скасувати</button>
          <button class="btn btn-danger" :disabled="deleting" @click="doDelete">
            {{ deleting ? "видаляємо…" : "Так, видалити" }}
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
import AnalysisResult from "@/components/analysis-components/common/AnalysisResult.vue";
import analysesApi from "@/api/analyses";

export default {
  name: "AnalysisDetailsView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent, AnalysisResult },
  data() {
    return {
      loading: false,
      sending: false,
      note: "",
      showDeleteModal: false,
      deleting: false,
    };
  },
  computed: {
    current() { return this.$store.state.analyses.current; },
    isDoctor() { return this.$store.getters["auth/isDoctor"]; },
    currentUser() { return this.$store.state.auth.user; },
    isOwner() {
      if (!this.current || !this.currentUser) return false;
      return this.current.userId === this.currentUser.id;
    },
    isDerma() {
      if (!this.current) return false;
      const t = String(this.current.type).toLowerCase();
      return t === "derma" || this.current.type === 5 || t === "5";
    },
    canReview() {
      if (!this.isDoctor || !this.current) return false;
      if (this.current.doctorReviewedAt) return false;
      const myId = this.currentUser?.id;
      if (!myId) return false;
      return this.current.userId && this.current.userId !== myId;
    },
  },
  async mounted() {
    this.loading = true;
    try {
      await this.$store.dispatch("analyses/loadOne", {
        id: this.$route.params.id,
        language: this.$locale,
      });
    } catch {
      this.$store.dispatch("flash", { type: "error", message: "не вдалось завантажити" });
    } finally {
      this.loading = false;
    }
  },
  watch: {
    "$locale"(newLang) {
      if (!this.current?.id) return;
      this.$store.dispatch("analyses/loadOne", {
        id: this.current.id,
        language: newLang,
      });
    },
  },
  methods: {
    async onReview() {
      const note = this.note.trim();
      if (!note) return;
      this.sending = true;
      try {
        await analysesApi.doctorReview(this.current.id, { note });
        await this.$store.dispatch("analyses/loadOne", this.current.id);
        this.note = "";
        this.$store.dispatch("flash", { type: "success", message: "коментар додано" });
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message:
            e.response?.data?.detail ||
            e.response?.data?.title ||
            (e.response?.status === 403
              ? "Немає активного зв'язку з цим пацієнтом — спочатку прийміть запрошення."
              : "не вдалось додати коментар"),
        });
      } finally {
        this.sending = false;
      }
    },

    async doDelete() {
      if (!this.current) return;
      this.deleting = true;
      try {
        await this.$store.dispatch("analyses/remove", this.current.id);
        this.$store.dispatch("flash", { type: "success", message: "аналіз видалено" });
        const idx = this.$store.state.analyses.list.findIndex(x => x.id === this.current.id);
        if (idx !== -1) this.$store.state.analyses.list.splice(idx, 1);
        this.showDeleteModal = false;
        this.$router.push("/analyses");
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || "не вдалось видалити аналіз",
        });
      } finally {
        this.deleting = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
.page-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.toolbar-actions {
  display: flex;
  gap: 0.8rem;
  flex-wrap: wrap;

  .btn {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 1.3rem;
    padding: 0.7rem 1.4rem;
    border-radius: 0.5rem;
    cursor: pointer;
    text-decoration: none;
    text-transform: none;

    &.btn-secondary {
      background: transparent;
      color: var(--purple);
      border: 1px solid var(--purple);
      &:hover { background: rgba(141, 50, 240, 0.06); }
    }

    &.btn-danger-ghost {
      background: transparent;
      color: #A32D2D;
      border: 1px solid #A32D2D;
      &:hover { background: #A32D2D; color: #fff; }
    }
  }
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
    }

    .modal-actions {
      display: flex;
      gap: 1rem;
      justify-content: flex-end;
      margin-top: 2rem;

      .btn {
        padding: 0.8rem 1.6rem;
        font-size: 1.3rem;
        border-radius: 0.5rem;
        cursor: pointer;
        border: 1px solid;
      }
      .btn-secondary {
        background: transparent;
        color: var(--black);
        border-color: #ccc;
      }
      .btn-danger {
        background: #A32D2D;
        color: #fff;
        border-color: #A32D2D;

        &:disabled { opacity: 0.6; cursor: not-allowed; }
      }
    }
  }
}

.link-back {
  background: transparent;
  color: var(--purple);
  font-size: 1.3rem;
  cursor: pointer;
  text-transform: none;
  font-family: inherit;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;

  &:hover { text-decoration: underline; }
}

.doctor-form {
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 2rem;
  margin-top: 1.5rem;

  h3 {
    font-size: 1.5rem;
    color: var(--purple);
    text-transform: uppercase;
    letter-spacing: 0.1rem;
    margin-bottom: 1rem;
    font-weight: 600;
  }

  .box {
    width: 100%;
    padding: 1rem 1.2rem;
    font-size: 1.4rem;
    border: var(--border);
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    text-transform: none;
    resize: vertical;

    &:focus { border-color: var(--purple); }
  }
}
</style>
