<template>
  <div class="user-menu" @click.stop>
    <div class="menu-head">
      <div class="avatar">{{ initials }}</div>
      <div class="info">
        <div class="name">{{ user.fullName || user.firstName }}</div>
        <div class="email">{{ user.email }}</div>
      </div>
    </div>

    <div class="menu-list">
      <router-link
        v-if="!isAdmin"
        to="/user-home"
        class="menu-item"
        @click="$emit('close')"
      >
        <i class="fa-solid fa-house"></i> {{ $t('nav.myDashboard') }}
      </router-link>
      <router-link
        v-if="isAdmin"
        to="/admin"
        class="menu-item"
        @click="$emit('close')"
      >
        <i class="fa-solid fa-gauge-high"></i> {{ $t('nav.adminPanel') }}
      </router-link>

      <router-link
        to="/profile"
        class="menu-item"
        @click="$emit('close')"
      >
        <i class="fa-solid fa-user-pen"></i> {{ $t('nav.myProfile') }}
      </router-link>

      <router-link
        v-if="!isAdmin"
        to="/analyses"
        class="menu-item"
        @click="$emit('close')"
      >
        <i class="fa-solid fa-flask"></i> {{ $t('nav.myAnalyses') }}
      </router-link>

      <router-link
        v-if="isDoctor"
        to="/patients"
        class="menu-item"
        @click="$emit('close')"
      >
        <i class="fa-solid fa-users"></i> {{ $t('nav.myPatients') }}
      </router-link>

      <div class="menu-divider"></div>

      <button class="menu-item logout-item" @click="onLogout">
        <i class="fa-solid fa-right-from-bracket"></i> {{ $t('nav.signOut') }}
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: "UserMenu",
  emits: ["close"],
  computed: {
    user() { return this.$store.state.auth.user || {}; },
    isAdmin() { return this.$store.getters["auth/isAdmin"]; },
    isDoctor() { return this.$store.getters["auth/isDoctor"]; },
    initials() {
      const fn = this.user.firstName || "";
      const ln = this.user.lastName || "";
      return ((fn[0] || "") + (ln[0] || "")).toUpperCase() || "?";
    },
  },
  methods: {
    async onLogout() {
      this.$emit("close");
      await this.$store.dispatch("auth/logout");
      this.$router.push("/");
    },
  },
};
</script>

<style scoped lang="scss">
.user-menu {
  position: absolute;
  top: 100%;
  right: 0;
  width: 28rem;
  background: white;
  border: var(--border);
  border-radius: 0.5rem;
  box-shadow: var(--box-shadow);
  margin-top: 1rem;
  overflow: hidden;
  z-index: 100;
}

.menu-head {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1.4rem;
  background: rgba(65, 90, 119, 0.04);
  border-bottom: var(--border);

  .avatar {
    width: 4rem;
    height: 4rem;
    border-radius: 50%;
    background: var(--purple);
    color: white;
    font-weight: 600;
    font-size: 1.4rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .info {
    min-width: 0;
    flex: 1;
  }

  .name {
    font-size: 1.4rem;
    color: var(--black);
    font-weight: 600;
    text-transform: none;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .email {
    font-size: 1.2rem;
    color: var(--light-color);
    text-transform: none;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

.menu-list {
  padding: 0.5rem 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem 1.4rem;
  font-size: 1.3rem;
  color: var(--black);
  cursor: pointer;
  text-transform: lowercase;
  background: transparent;
  border: none;
  width: 100%;
  text-align: left;
  font-family: inherit;

  i {
    width: 1.6rem;
    color: var(--purple);
    font-size: 1.4rem;
  }

  &:hover {
    background: rgba(65, 90, 119, 0.06);
  }
}

.menu-divider {
  height: 1px;
  background: rgba(0, 0, 0, 0.06);
  margin: 0.5rem 0;
}

.logout-item {
  color: #A32D2D;

  i { color: #A32D2D; }

  &:hover {
    background: rgba(226, 75, 74, 0.06);
  }
}
</style>
