<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <h1 class="page-title">{{ $t('admin.usersPage.pageTitle') }}</h1>

    <div class="admin-toolbar">
      <input
        v-model="search"
        type="text"
        class="box search"
        :placeholder="$t('admin.usersPage.searchPlaceholder')"
        @input="debouncedLoad"
      />
      <select v-model="roleFilter" class="box" @change="load">
        <option value="">{{ $t('admin.usersPage.allRoles') }}</option>
        <option value="Administrator">Administrator</option>
        <option value="Doctor">Doctor</option>
        <option value="User">User</option>
      </select>
    </div>

    <div v-if="loading" class="loader">{{ $t('admin.usersPage.loading') }}</div>

    <table v-else class="table">
      <thead>
        <tr>
          <th>{{ $t('admin.usersPage.tableEmail') }}</th>
          <th>{{ $t('admin.usersPage.tableName') }}</th>
          <th>{{ $t('admin.usersPage.tableRoles') }}</th>
          <th>{{ $t('admin.usersPage.tableStatus') }}</th>
          <th>{{ $t('admin.usersPage.tableRegistered') }}</th>
          <th>{{ $t('admin.usersPage.tableActions') }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.id">
          <td>{{ u.email }}</td>
          <td>{{ u.firstName }} {{ u.lastName }}</td>
          <td>
            <span v-for="r in u.roles" :key="r" class="role-pill">{{ r }}</span>
          </td>
          <td>
            <span v-if="u.isBanned" class="badge badge-urgent">{{ $t('admin.usersPage.statusBanned') }}</span>
            <span v-else class="badge badge-normal">{{ $t('admin.usersPage.statusActive') }}</span>
          </td>
          <td>{{ formatDate(u.createdAt) }}</td>
          <td>
            <button class="link-action" @click="onChangeRole(u)">{{ $t('admin.usersPage.actionChangeRole') }}</button>
            <button v-if="!u.isBanned" class="link-action danger" @click="onBan(u)">
              {{ $t('admin.usersPage.actionBan') }}
            </button>
            <button v-else class="link-action" @click="onUnban(u)">
              {{ $t('admin.usersPage.actionUnban') }}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import { adminApi } from "@/api/users";

export default {
  name: "AdminUsersView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent },
  data() {
    return {
      loading: false,
      users: [],
      search: "",
      roleFilter: "",
      searchTimer: null,
    };
  },
  mounted() { this.load(); },
  methods: {
    debouncedLoad() {
      clearTimeout(this.searchTimer);
      this.searchTimer = setTimeout(this.load, 350);
    },
    async load() {
      this.loading = true;
      try {
        const params = { pageSize: 50 };
        if (this.search) params.search = this.search;
        if (this.roleFilter) params.role = this.roleFilter;
        const { data } = await adminApi.listUsers(params);
        this.users = data.items || data;
      } catch {
        this.$store.dispatch("flash", { type: "error", message: this.$t('admin.usersPage.loadError') });
      } finally {
        this.loading = false;
      }
    },
    async onBan(u) {
      const reason = prompt(this.$t('admin.usersPage.banPrompt'));
      if (reason === null) return;
      try {
        await adminApi.banUser(u.id, reason);
        this.$store.dispatch("flash", { type: "success", message: this.$t('admin.usersPage.banSuccess') });
        await this.load();
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('admin.usersPage.errorGeneric'),
        });
      }
    },
    async onUnban(u) {
      try {
        await adminApi.unbanUser(u.id);
        this.$store.dispatch("flash", { type: "success", message: this.$t('admin.usersPage.unbanSuccess') });
        await this.load();
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('admin.usersPage.errorGeneric'),
        });
      }
    },
    async onChangeRole(u) {
      const role = prompt(this.$t('admin.usersPage.rolePrompt'), u.roles?.[0] || "User");
      if (!role) return;
      try {
        await adminApi.changeRole(u.id, role);
        this.$store.dispatch("flash", { type: "success", message: this.$t('admin.usersPage.roleUpdated') });
        await this.load();
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('admin.usersPage.errorGeneric'),
        });
      }
    },
    formatDate(iso) {
      if (!iso) return "—";
      const lang = this.$locale === "en" ? "en-US" : "uk-UA";
      return new Date(iso).toLocaleDateString(lang);
    },
  },
};
</script>

<style scoped lang="scss">
.admin-toolbar {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;

  .box {
    padding: 0.8rem 1.2rem;
    font-size: 1.4rem;
    border: var(--border);
    border-radius: 0.4rem;
    text-transform: none;
    background: white;

    &:focus { border-color: var(--purple); }
  }

  .search { flex: 1; min-width: 24rem; }
}

.role-pill {
  display: inline-block;
  font-size: 1.1rem;
  background: rgba(65, 90, 119, 0.1);
  color: var(--purple);
  padding: 0.2rem 0.7rem;
  border-radius: 0.3rem;
  margin-right: 0.3rem;
  text-transform: lowercase;
}

.link-action {
  background: transparent;
  color: var(--purple);
  font-size: 1.2rem;
  cursor: pointer;
  padding: 0.3rem 0.6rem;
  font-family: inherit;
  text-transform: lowercase;

  &:hover { text-decoration: underline; }
  &.danger { color: #A32D2D; }
}
</style>
