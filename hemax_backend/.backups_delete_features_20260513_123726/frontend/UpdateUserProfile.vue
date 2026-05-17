<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <h1 class="page-title">редагування профілю</h1>

    <form class="profile-form" @submit.prevent="onSave">
      <div class="row two-cols">
        <div>
          <span>ім'я</span>
          <input v-model="form.firstName" type="text" class="box" />
        </div>
        <div>
          <span>прізвище</span>
          <input v-model="form.lastName" type="text" class="box" />
        </div>
      </div>

      <div class="row two-cols">
        <div>
          <span>дата народження</span>
          <input v-model="form.dateOfBirth" type="date" class="box" />
        </div>
        <div>
          <span>стать</span>
          <select v-model="form.sex" class="box">
            <option value="Unknown">не вказано</option>
            <option value="Male">чоловіча</option>
            <option value="Female">жіноча</option>
          </select>
        </div>
      </div>

      <div class="row">
        <span>email (не редагується)</span>
        <input :value="user.email" type="email" class="box" disabled />
      </div>

      <button type="submit" class="btn" :disabled="saving">
        {{ saving ? "зберігаємо…" : "зберегти зміни" }}
      </button>
    </form>

    <section class="password-block">
      <h2>зміна паролю</h2>
      <form class="profile-form" @submit.prevent="onChangePass">
        <div class="row">
          <span>поточний пароль</span>
          <input v-model="passForm.current" type="password" class="box" required />
        </div>
        <div class="row">
          <span>новий пароль</span>
          <input v-model="passForm.next" type="password" class="box" required />
        </div>
        <button type="submit" class="btn" :disabled="passSaving">
          {{ passSaving ? "змінюємо…" : "змінити пароль" }}
        </button>
      </form>
    </section>
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
    };
  },
  computed: {
    user() { return this.$store.state.auth.user || {}; },
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
        this.$store.dispatch("flash", { type: "success", message: "профіль оновлено" });
      } catch (e) {
        this.$store.dispatch("flash", { type: "error", message: e.response?.data?.detail || "помилка" });
      } finally {
        this.saving = false;
      }
    },
    async onChangePass() {
      this.passSaving = true;
      try {
        await usersApi.changePassword(this.passForm.current, this.passForm.next);
        this.passForm = { current: "", next: "" };
        this.$store.dispatch("flash", { type: "success", message: "пароль змінено" });
      } catch (e) {
        this.$store.dispatch("flash", { type: "error", message: e.response?.data?.detail || "не вдалось" });
      } finally {
        this.passSaving = false;
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

@media (max-width: 600px) {
  .profile-form .row.two-cols { grid-template-columns: 1fr; }
}
</style>
