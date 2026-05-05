<template>
  <div class="navbar">
    <router-link to="/" exact-active-class="active">{{ $t('nav.home') }}</router-link>
    <router-link v-if="isAuth" to="/analyses" active-class="active">{{ $t('nav.myAnalyses') }}</router-link>
    <router-link v-if="isDoctor" to="/patients" active-class="active">{{ $t('nav.patients') }}</router-link>
    <router-link to="/blog" active-class="active">{{ $t('nav.blog') }}</router-link>
    <router-link to="/contacts" active-class="active">{{ $t('nav.contacts') }}</router-link>
    <router-link to="/faq" active-class="active">{{ $t('nav.faq') }}</router-link>
    <router-link v-if="isAdmin" to="/admin" active-class="active">{{ $t('nav.admin') }}</router-link>
  </div>
</template>

<script>
export default {
  name: "NavbarComponent",
  computed: {
    isAuth() { return this.$store.state.auth.isAuth; },
    isAdmin() { return this.$store.getters["auth/isAdmin"]; },
    isDoctor() { return this.$store.getters["auth/isDoctor"]; },
  },
};
</script>

<style scoped lang="scss">
@import "navbar";
</style>
