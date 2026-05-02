<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />
  <ContactsComponent />
  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import ContactsComponent from "@/components/UI/contacts/contacts-component.vue";

export default {
  name: "ContactsView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent, ContactsComponent },
};
</script>
