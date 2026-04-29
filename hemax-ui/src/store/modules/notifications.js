import { notificationsApi } from '@/api/users';

export default {
  namespaced: true,
  state: () => ({
    list: [],
    unreadCount: 0,
  }),
  mutations: {
    setList(state, items) {
      state.list = items;
      state.unreadCount = items.filter((n) => !n.isRead).length;
    },
    setUnreadCount(state, count) {
      state.unreadCount = count;
    },
    markRead(state, id) {
      const n = state.list.find((x) => x.id === id);
      if (n && !n.isRead) {
        n.isRead = true;
        state.unreadCount = Math.max(0, state.unreadCount - 1);
      }
    },
    markAllRead(state) {
      state.list = state.list.map((n) => ({ ...n, isRead: true }));
      state.unreadCount = 0;
    },
    reset(state) {
      state.list = [];
      state.unreadCount = 0;
    },
  },
  actions: {
    async load({ commit }) {
      const { data } = await notificationsApi.list({ pageSize: 50 });
      commit('setList', data.items || []);
    },
    async loadUnreadCount({ commit }) {
      const { data } = await notificationsApi.unreadCount();
      const n = typeof data === 'number' ? data : (data.count ?? 0);
      commit('setUnreadCount', n);
    },
    async markRead({ commit }, id) {
      await notificationsApi.markRead(id);
      commit('markRead', id);
    },
    async markAllRead({ commit }) {
      await notificationsApi.markAllRead();
      commit('markAllRead');
    },
  },
};
