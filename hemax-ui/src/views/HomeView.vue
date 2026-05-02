<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />
  <HeroComponent />
  <FeaturesComponent />
  <NewsletterComponent />
  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import HeroComponent from "@/components/UI/hero/hero-component.vue";
import FeaturesComponent from "@/components/UI/features/features-component.vue";
import NewsletterComponent from "@/components/UI/newsletter/newsletter-component.vue";

export default {
  name: "HomeView",
  components: {
    HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent,
    HeroComponent, FeaturesComponent, NewsletterComponent,
  },
};
</script>
