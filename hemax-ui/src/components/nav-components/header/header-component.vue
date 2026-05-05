<template>
  <div class="header">
    <router-link to="/" class="logo">
      <i class="fa-solid fa-stethoscope"></i> hemax
    </router-link>

    <form class="search-form" @submit.prevent="onSearch">
      <input
        v-model="searchInput"
        type="search"
        :placeholder="$t('header.searchPlaceholder')"
        id="search-box"
      />
      <label for="search-box" class="fas fa-search" @click="onSearch"></label>
    </form>

    <div class="icons">
      <LanguageSwitcher class="lang-switcher-header" />

      <router-link
        to="/contacts"
        class="fa-solid fa-address-book"
        :title="$t('header.contactsHint')"
      ></router-link>
      <router-link
        to="/faq"
        class="fa-solid fa-circle-question"
        :title="$t('header.faqHint')"
      ></router-link>

      <div
        v-if="isAuth"
        class="bell-wrap"
        @click.stop="toggleNotifications"
        tabindex="0"
        :title="$t('header.notificationsHint')"
      >
        <i class="fa-solid fa-bell"></i>
        <span v-if="unreadCount > 0" class="bell-badge">{{ unreadCount }}</span>
        <NotificationsDropdown v-if="showNotifications" @close="showNotifications = false" />
      </div>

      <div
        v-if="isAuth"
        class="user-wrap"
        @click.stop="toggleUserMenu"
        tabindex="0"
      >
        <i class="fa-solid fa-user" :title="$t('header.profileHint')"></i>
        <UserMenu v-if="showUserMenu" @close="showUserMenu = false" />
      </div>

      <router-link
        v-else
        to="/sign-in"
        class="sign-in-link"
      >{{ $t('nav.signIn') }}</router-link>
    </div>
  </div>
</template>

<script>
import NotificationsDropdown from "@/components/notification-components/NotificationsDropdown.vue";
import UserMenu from "./UserMenu.vue";
import LanguageSwitcher from "@/components/UI/LanguageSwitcher.vue";

export default {
  name: "HeaderComponent",
  components: { NotificationsDropdown, UserMenu, LanguageSwitcher },
  data() {
    return {
      searchInput: "",
      showNotifications: false,
      showUserMenu: false,
    };
  },
  computed: {
    isAuth() { return this.$store.state.auth.isAuth; },
    isAdmin() { return this.$store.getters["auth/isAdmin"]; },
    unreadCount() { return this.$store.state.notifications.unreadCount; },
  },
  watch: {
    searchInput(val) {
      this.$store.commit("searchInput", val);
    },
    isAuth(v) {
      if (v) this.$store.dispatch("notifications/load").catch(() => {});
    },
  },
  mounted() {
    this.searchInput = this.$store.state.search || "";
    if (this.isAuth) {
      this.$store.dispatch("notifications/load").catch(() => {});
    }
    this._notifTimer = setInterval(() => {
      if (this.isAuth) {
        this.$store.dispatch("notifications/load").catch(() => {});
      }
    }, 30000);
    document.addEventListener("click", this.closeAll);
  },
  beforeUnmount() {
    if (this._notifTimer) clearInterval(this._notifTimer);
    document.removeEventListener("click", this.closeAll);
  },
  methods: {
    onSearch() {
      const q = this.searchInput.trim();
      if (!q) return;
      this.$router.push({ name: "analyses", query: { q } });
    },
    toggleNotifications() {
      this.showNotifications = !this.showNotifications;
      this.showUserMenu = false;
    },
    toggleUserMenu() {
      this.showUserMenu = !this.showUserMenu;
      this.showNotifications = false;
    },
    closeAll() {
      // Click anywhere outside drops both panels
      this.showNotifications = false;
      this.showUserMenu = false;
    },
  },
};
</script>

<style scoped lang="scss">
@import "header-style";

.lang-switcher-header {
  margin-right: 0.4rem;
}
</style>
