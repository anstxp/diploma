<template>
  <div class="login-form-container">
    <form @submit.prevent="onSubmit">
      <h3>{{ $t('auth.signIn.title') }}</h3>

      <div class="form-row">
        <span>{{ $t('auth.signIn.emailLabel') }}</span>
        <input
          v-model="email"
          type="email"
          class="box"
          :placeholder="$t('auth.signIn.emailPlaceholder')"
          required
        />
      </div>

      <div class="form-row">
        <span>{{ $t('auth.signIn.passwordLabel') }}</span>
        <input
          v-model="password"
          type="password"
          class="box"
          :placeholder="$t('auth.signIn.passwordPlaceholder')"
          required
        />
      </div>

      <button type="submit" class="btn" :disabled="loading">
        {{ loading ? $t('auth.signIn.submitting') : $t('auth.signIn.submitButton') }}
      </button>

      <p>
        {{ $t('auth.signIn.noAccount') }}
        <router-link to="/sign-up">{{ $t('auth.signIn.signUpLink') }}</router-link>
      </p>

      <div class="demo-block">
        <span class="demo-title">{{ $t('auth.signIn.demoTitle') }}</span>
        <button type="button" class="light-button" @click="fillDemo('admin')">
          {{ $t('auth.signIn.demoAdmin') }}
        </button>
        <button type="button" class="light-button" @click="fillDemo('doctor')">
          {{ $t('auth.signIn.demoDoctor') }}
        </button>
        <button type="button" class="light-button" @click="fillDemo('patient')">
          {{ $t('auth.signIn.demoPatient') }}
        </button>
      </div>
    </form>
  </div>
</template>

<script>
export default {
  name: "SignInComponent",
  data() {
    return { email: "", password: "", loading: false };
  },
  methods: {
    fillDemo(role) {
      const demos = {
        admin: ["admin@hemax.local", "Admin#12345"],
        doctor: ["doctor@hemax.local", "Doctor#12345"],
        patient: ["patient@hemax.local", "Patient#12345"],
      };
      [this.email, this.password] = demos[role];
    },
    async onSubmit() {
      this.loading = true;
      try {
        await this.$store.dispatch("auth/login", {
          email: this.email,
          password: this.password,
        });
        const redirect = this.$route.query.redirect || "/";
        this.$router.push(redirect);
      } catch {
        // flash already shown
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
@import "auth-style";
</style>
