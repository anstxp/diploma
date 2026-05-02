<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />
  <FaqComponent />
  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import FaqComponent from "@/components/UI/faq/faq-component.vue";

export default {
  name: "FAQView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent, FaqComponent },
};
</script>
