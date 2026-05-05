<template>
  <div class="bottom-navbar">
    <router-link to="/" exact-active-class="active" :title="$t('nav.home')">
      <i class="fas fa-home"></i>
    </router-link>
    <router-link
      v-if="isAuth"
      to="/analyses"
      active-class="active"
      :title="$t('nav.myAnalyses')"
    ><i class="fas fa-flask"></i></router-link>
    <router-link to="/blog" active-class="active" :title="$t('nav.blog')">
      <i class="fa-solid fa-book-open"></i>
    </router-link>
    <router-link
      v-if="isAuth"
      :to="isAdmin ? '/admin' : '/user-home'"
      active-class="active"
      :title="isAdmin ? $t('nav.adminPanel') : $t('nav.myDashboard')"
    ><i class="fas fa-user"></i></router-link>
    <router-link
      v-else
      to="/sign-in"
      active-class="active"
      :title="$t('nav.signIn')"
    ><i class="fas fa-sign-in-alt"></i></router-link>
  </div>
</template>

<script>
export default {
  name: "BottomNavbarComponent",
  computed: {
    isAuth() { return this.$store.state.auth.isAuth; },
    isAdmin() { return this.$store.getters["auth/isAdmin"]; },
  },
};
</script>

<style scoped lang="scss">
@import "bottom-navbar-style";
</style>
