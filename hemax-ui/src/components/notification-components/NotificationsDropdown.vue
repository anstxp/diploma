<template>
  <div class="dropdown" @click.stop>
    <div class="dropdown-head">
      <span>{{ $t('notifications.title') }}</span>
      <button class="link-btn" @click="markAll" v-if="unreadCount > 0">
        {{ $t('notifications.markAllShort') }}
      </button>
    </div>

    <div class="list" v-if="list.length > 0">
      <div
        v-for="n in list"
        :key="n.id"
        :class="['item', { unread: !n.isRead }]"
        @click="open(n)"
      >
        <div class="dot"></div>
        <div class="body">
          <div class="title">{{ n.title }}</div>
          <div class="text">{{ n.body }}</div>
          <div class="time">{{ formatTime(n.createdAt) }}</div>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <i class="fa-solid fa-bell-slash"></i>
      <span>{{ $t('notifications.emptyShort') }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: "NotificationsDropdown",
  emits: ["close"],
  computed: {
    list() { return this.$store.state.notifications.list.slice(0, 10); },
    unreadCount() { return this.$store.state.notifications.unreadCount; },
  },
  methods: {
    markAll() {
      this.$store.dispatch("notifications/markAllRead");
    },
    async open(n) {
      if (!n.isRead) await this.$store.dispatch("notifications/markRead", n.id);
      if (n.link) {
        this.$router.push(n.link);
      }
      this.$emit("close");
    },
    formatTime(iso) {
      if (!iso) return "";
      const d = new Date(iso);
      const diffMs = Date.now() - d.getTime();
      const min = Math.floor(diffMs / 60000);
      if (min < 1)  return this.$t('notifications.timeAgo.now');
      if (min < 60) return this.$t('notifications.timeAgo.minutes', { n: min });
      const h = Math.floor(min / 60);
      if (h < 24)   return this.$t('notifications.timeAgo.hours', { n: h });
      const lang = this.$locale === "en" ? "en-US" : "uk-UA";
      return d.toLocaleDateString(lang);
    },
  },
};
</script>

<style scoped lang="scss">
.dropdown {
  position: absolute;
  top: 100%;
  right: 0;
  width: 36rem;
  max-height: 50rem;
  background: white;
  border: var(--border);
  border-radius: 0.5rem;
  box-shadow: var(--box-shadow);
  margin-top: 1rem;
  overflow: hidden;
  z-index: 100;
  display: flex;
  flex-direction: column;
}

.dropdown-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.4rem;
  border-bottom: var(--border);
  font-size: 1.3rem;
  color: var(--black);
  text-transform: uppercase;
  letter-spacing: 0.1rem;
  font-weight: 500;
}

.link-btn {
  background: none;
  color: var(--purple);
  font-size: 1.2rem;
  cursor: pointer;
  text-transform: lowercase;
  letter-spacing: 0;
  font-family: inherit;

  &:hover { text-decoration: underline; }
}

.list {
  overflow-y: auto;
  max-height: 40rem;
}

.item {
  display: flex;
  gap: 1rem;
  padding: 1rem 1.4rem;
  border-bottom: 1px solid rgba(0,0,0,0.05);
  cursor: pointer;
  transition: background 0.15s;

  &:hover { background: rgba(65, 90, 119, 0.04); }

  &.unread {
    background: rgba(65, 90, 119, 0.04);
    .dot { background: var(--purple); }
  }

  .dot {
    width: 0.8rem;
    height: 0.8rem;
    border-radius: 50%;
    background: transparent;
    margin-top: 0.6rem;
    flex-shrink: 0;
  }

  .body { flex: 1; min-width: 0; }
  .title {
    font-size: 1.3rem;
    font-weight: 500;
    color: var(--black);
    margin-bottom: 0.2rem;
    text-transform: none;
  }
  .text {
    font-size: 1.2rem;
    color: var(--light-color);
    text-transform: none;
    overflow: hidden;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
  }
  .time {
    font-size: 1.1rem;
    color: var(--light-color);
    margin-top: 0.4rem;
    text-transform: none;
  }
}

.empty {
  padding: 3rem 2rem;
  text-align: center;
  color: var(--light-color);
  font-size: 1.3rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.6rem;

  i { font-size: 2.4rem; }
}
</style>
