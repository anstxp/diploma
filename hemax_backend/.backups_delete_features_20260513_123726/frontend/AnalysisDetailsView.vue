<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <button class="link-back" @click="$router.back()">
      <i class="fa-solid fa-arrow-left"></i> назад
    </button>

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
    return { loading: false, sending: false, note: "" };
  },
  computed: {
    current() { return this.$store.state.analyses.current; },
    isDoctor() { return this.$store.getters["auth/isDoctor"]; },
    currentUser() { return this.$store.state.auth.user; },
    canReview() {
      // Doctor can leave a review only when:
      //   - they are looking at someone else's analysis
      //   - the analysis hasn't been reviewed yet
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
      await this.$store.dispatch("analyses/loadOne", this.$route.params.id);
    } catch {
      this.$store.dispatch("flash", { type: "error", message: "не вдалось завантажити" });
    } finally {
      this.loading = false;
    }
  },
  methods: {
    async onReview() {
      const note = this.note.trim();
      if (!note) return;
      this.sending = true;
      try {
        // Backend returns the updated AnalysisDto, but we reload the full
        // detail so result/raw JSON stay populated and the form hides
        // (v-if depends on current.doctorReviewedAt being set).
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
  },
};
</script>

<style scoped lang="scss">
.link-back {
  background: transparent;
  color: var(--purple);
  font-size: 1.3rem;
  cursor: pointer;
  margin-bottom: 1.5rem;
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
