<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <h1 class="page-title">{{ $t('profileUpdate.title') }}</h1>

    <form class="profile-form" @submit.prevent="onSave">
      <div class="row two-cols">
        <div>
          <span>{{ $t('profileUpdate.firstName') }}</span>
          <input v-model="form.firstName" type="text" class="box" />
        </div>
        <div>
          <span>{{ $t('profileUpdate.lastName') }}</span>
          <input v-model="form.lastName" type="text" class="box" />
        </div>
      </div>

      <div class="row two-cols">
        <div>
          <span>{{ $t('profileUpdate.dateOfBirth') }}</span>
          <input v-model="form.dateOfBirth" type="date" class="box" />
        </div>
        <div>
          <span>{{ $t('profileUpdate.sex') }}</span>
          <select v-model="form.sex" class="box">
            <option value="Unknown">{{ $t('profileUpdate.sexUnknown') }}</option>
            <option value="Male">{{ $t('profileUpdate.sexMale') }}</option>
            <option value="Female">{{ $t('profileUpdate.sexFemale') }}</option>
          </select>
        </div>
      </div>

      <div class="row">
        <span>{{ $t('profileUpdate.emailLockedLabel') }}</span>
        <input :value="user.email" type="email" class="box" disabled />
      </div>

      <button type="submit" class="btn" :disabled="saving">
        {{ saving ? $t('profileUpdate.saving') : $t('profileUpdate.saveButton') }}
      </button>
    </form>

    <section class="password-block">
      <h2>{{ $t('profileUpdate.passwordTitle') }}</h2>
      <form class="profile-form" @submit.prevent="onChangePass">
        <div class="row">
          <span>{{ $t('profileUpdate.currentPasswordLabel') }}</span>
          <input v-model="passForm.current" type="password" class="box" required />
        </div>
        <div class="row">
          <span>{{ $t('profileUpdate.newPasswordLabel') }}</span>
          <input v-model="passForm.next" type="password" class="box" required />
        </div>
        <button type="submit" class="btn" :disabled="passSaving">
          {{ passSaving ? $t('profileUpdate.changingPassword') : $t('profileUpdate.changePasswordButton') }}
        </button>
      </form>
    </section>

    <!-- ─────────────────────────────────────────────────────────────────
         DANGER ZONE — account deletion (GDPR right-to-erasure)
    ───────────────────────────────────────────────────────────────── -->
    <section class="danger-zone">
      <h2><i class="fa-solid fa-triangle-exclamation"></i> {{ $t('profileUpdate.dangerZoneTitle') }}</h2>
      <div class="danger-card">
        <h3>{{ $t('profileUpdate.deleteAccountTitle') }}</h3>
        <p>{{ $t('profileUpdate.deleteAccountBody') }}</p>
        <button class="btn btn-danger" @click="showDeleteModal = true">
          <i class="fa-solid fa-trash"></i> {{ $t('profileUpdate.deleteAccountButton') }}
        </button>
      </div>
    </section>

    <div v-if="showDeleteModal" class="modal-overlay" @click.self="cancelDelete">
      <div class="modal">
        <h3>
          <i class="fa-solid fa-triangle-exclamation"></i>
          {{ $t('profileUpdate.deleteModalTitle') }}
        </h3>
        <p>{{ $t('profileUpdate.deleteModalThisDeletes') }}</p>
        <ul class="impact-list">
          <li>{{ $t('profileUpdate.deleteListAnalyses') }}</li>
          <li>{{ $t('profileUpdate.deleteListProfile') }}</li>
          <li>{{ $t('profileUpdate.deleteListDoctors') }}</li>
          <li>{{ $t('profileUpdate.deleteListNotifications') }}</li>
          <li>{{ $t('profileUpdate.deleteListSessions') }}</li>
        </ul>
        <p v-html="confirmHintHtml"></p>
        <input
          v-model="confirmEmail"
          type="email"
          class="box confirm-input"
          :placeholder="user.email"
          autocomplete="off"
        />
        <div class="modal-actions">
          <button class="btn btn-secondary" :disabled="deleting" @click="cancelDelete">
            {{ $t('profileUpdate.deleteModalCancel') }}
          </button>
          <button
            class="btn btn-danger"
            :disabled="!canConfirm || deleting"
            @click="onDeleteAccount"
          >
            {{ deleting ? $t('profileUpdate.deleting') : $t('profileUpdate.deleteModalConfirm') }}
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
import { usersApi } from "@/api/users";

export default {
  name: "UpdateUserProfile",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent },
  data() {
    return {
      saving: false, passSaving: false,
      form: { firstName: "", lastName: "", dateOfBirth: "", sex: "Unknown" },
      passForm: { current: "", next: "" },
      showDeleteModal: false,
      deleting: false,
      confirmEmail: "",
    };
  },
  computed: {
    user() { return this.$store.state.auth.user || {}; },
    canConfirm() {
      return this.confirmEmail.trim().toLowerCase()
          === (this.user.email || "").trim().toLowerCase();
    },
    confirmHintHtml() {
      const safeEmail = String(this.user.email || "")
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      return this.$t('profileUpdate.deleteModalConfirmHint', {
        email: `<strong>${safeEmail}</strong>`,
      });
    },
  },
  mounted() {
    const u = this.user;
    this.form.firstName = u.firstName || "";
    this.form.lastName = u.lastName || "";
    this.form.dateOfBirth = u.dateOfBirth ? u.dateOfBirth.slice(0, 10) : "";
    this.form.sex = u.sex || "Unknown";
  },
  methods: {
    async onSave() {
      this.saving = true;
      try {
        const { data } = await usersApi.updateProfile({ ...this.form });
        this.$store.commit("auth/setUser", data);
        this.$store.dispatch("flash", { type: "success", message: this.$t('profileUpdate.successProfile') });
      } catch (e) {
        this.$store.dispatch("flash", { type: "error", message: e.response?.data?.detail || this.$t('profileUpdate.errorProfile') });
      } finally {
        this.saving = false;
      }
    },
    async onChangePass() {
      this.passSaving = true;
      try {
        await usersApi.changePassword(this.passForm.current, this.passForm.next);
        this.passForm = { current: "", next: "" };
        this.$store.dispatch("flash", { type: "success", message: this.$t('profileUpdate.successPassword') });
      } catch (e) {
        this.$store.dispatch("flash", { type: "error", message: e.response?.data?.detail || this.$t('profileUpdate.errorPassword') });
      } finally {
        this.passSaving = false;
      }
    },

    cancelDelete() {
      if (this.deleting) return;
      this.showDeleteModal = false;
      this.confirmEmail = "";
    },

    async onDeleteAccount() {
      if (!this.canConfirm) return;
      this.deleting = true;
      try {
        await usersApi.deleteAccount();
        this.$store.dispatch("flash", {
          type: "success",
          message: this.$t('profileUpdate.successDelete'),
        });
        try { await this.$store.dispatch("auth/logout"); } catch { /* ignore */ }
        this.$router.push("/login");
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message:
            e.response?.data?.detail ||
            e.response?.data?.title ||
            this.$t('profileUpdate.errorDelete'),
        });
        this.deleting = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
.profile-form {
  max-width: 60rem;
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 2rem;
  margin-bottom: 2rem;

  .row { margin-bottom: 1rem; }
  .row.two-cols {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
  .row > span, .row > div > span {
    display: block;
    font-size: 1.3rem;
    color: var(--black);
    margin-bottom: 0.4rem;
    text-transform: lowercase;
  }
  .box {
    width: 100%;
    padding: 0.9rem 1.2rem;
    font-size: 1.4rem;
    border: var(--border);
    border-radius: 0.5rem;
    text-transform: none;
    background: white;

    &:disabled {
      background: rgba(0,0,0,0.04);
      cursor: not-allowed;
    }
    &:focus:not(:disabled) { border-color: var(--purple); }
  }
}

.password-block h2 {
  font-size: 2rem;
  color: var(--black);
  margin-bottom: 1rem;
  font-weight: 500;
  text-transform: none;
}

.danger-zone {
  margin-top: 4rem;
  padding-top: 2rem;
  border-top: 2px solid #fee2e2;

  h2 {
    font-size: 1.7rem;
    color: #A32D2D;
    margin-bottom: 1rem;
    font-weight: 600;
    text-transform: none;
    display: inline-flex;
    align-items: center;
    gap: 0.6rem;
    i { color: #f59e0b; }
  }

  .danger-card {
    max-width: 60rem;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 0.6rem;
    padding: 2rem;

    h3 {
      font-size: 1.5rem;
      color: #7f1d1d;
      margin-bottom: 0.8rem;
      font-weight: 600;
      text-transform: none;
    }
    p {
      font-size: 1.35rem;
      color: var(--black);
      line-height: 1.6;
      text-transform: none;
      margin-bottom: 1.5rem;
    }
  }

  .btn-danger {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: #A32D2D;
    color: #fff;
    border: 1px solid #A32D2D;
    padding: 0.9rem 1.6rem;
    font-size: 1.35rem;
    border-radius: 0.5rem;
    cursor: pointer;
    text-transform: none;
    &:hover { background: #7f1d1d; }
  }
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;

  .modal {
    background: #fff;
    border-radius: 12px;
    padding: 2.5rem;
    max-width: 520px;
    width: 100%;
    box-shadow: 0 20px 60px rgba(0,0,0,0.35);
    max-height: 90vh;
    overflow-y: auto;

    h3 {
      font-size: 1.8rem;
      color: #A32D2D;
      margin-bottom: 1.2rem;
      display: flex;
      align-items: flex-start;
      gap: 0.7rem;
      text-transform: none;
      font-weight: 600;
      i { color: #f59e0b; flex-shrink: 0; }
    }
    p {
      font-size: 1.4rem;
      color: var(--black);
      line-height: 1.55;
      margin-bottom: 1rem;
      text-transform: none;
    }
    .impact-list {
      margin: 0 0 1.5rem 2rem;
      padding: 0;
      li {
        font-size: 1.3rem;
        color: var(--black);
        line-height: 1.6;
        margin-bottom: 0.3rem;
        list-style: disc;
      }
    }
    .confirm-input {
      width: 100%;
      padding: 0.9rem 1.2rem;
      font-size: 1.4rem;
      border: 2px solid #fecaca;
      border-radius: 0.5rem;
      margin-bottom: 1.5rem;
      text-transform: none;
      &:focus { border-color: #A32D2D; outline: none; }
    }
    .modal-actions {
      display: flex;
      gap: 1rem;
      justify-content: flex-end;
      flex-wrap: wrap;

      .btn {
        padding: 0.9rem 1.6rem;
        font-size: 1.35rem;
        border-radius: 0.5rem;
        cursor: pointer;
        border: 1px solid;
        text-transform: none;
        &:disabled { opacity: 0.5; cursor: not-allowed; }
      }
      .btn-secondary {
        background: transparent;
        color: var(--black);
        border-color: #ccc;
        &:hover:not(:disabled) { background: #f5f5f5; }
      }
      .btn-danger {
        background: #A32D2D;
        color: #fff;
        border-color: #A32D2D;
        &:hover:not(:disabled) { background: #7f1d1d; }
      }
    }
  }
}

@media (max-width: 600px) {
  .profile-form .row.two-cols { grid-template-columns: 1fr; }
}
</style>
