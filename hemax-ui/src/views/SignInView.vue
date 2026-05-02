<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />
  <SignInComponent />
  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import SignInComponent from "@/components/auth-components/sign-in-component.vue";

export default {
  name: "SignInView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent, SignInComponent },
};
</script>
