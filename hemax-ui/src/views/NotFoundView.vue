<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page not-found">
    <div class="content">
      <div class="big">404</div>
      <h2>{{ $t('notFound.title') }}</h2>
      <p>{{ $t('notFound.body') }}</p>
      <router-link to="/" class="btn">{{ $t('common.goHome') }}</router-link>
    </div>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";

export default {
  name: "NotFoundView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent },
};
</script>

<style scoped lang="scss">
.not-found {
  min-height: calc(100vh - 26rem);
  display: flex;
  align-items: center;
  justify-content: center;

  .content {
    text-align: center;
    max-width: 50rem;

    .big {
      font-size: 12rem;
      font-weight: 700;
      color: var(--purple);
      line-height: 1;
      margin-bottom: 1rem;
    }

    h2 {
      font-size: 2.4rem;
      color: var(--black);
      margin-bottom: 1rem;
      text-transform: lowercase;
    }

    p {
      font-size: 1.5rem;
      color: var(--light-color);
      margin-bottom: 1.5rem;
      text-transform: none;
    }
  }
}
</style>
