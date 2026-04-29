import authApi from '@/api/auth';
import { t } from '@/i18n';

const STORAGE_KEY = 'hemax_session';

function loadSession() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function saveSession(payload) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
}

function clearSession() {
  localStorage.removeItem(STORAGE_KEY);
}

let _crossTabBound = false;
function bindCrossTabSync(store) {
  if (_crossTabBound) return;
  _crossTabBound = true;
  if (typeof window === 'undefined') return;

  window.addEventListener('storage', (event) => {
    if (event.key !== STORAGE_KEY) return;

    if (!event.newValue) {
      // Logged out somewhere else.
      const wasAuth = store.state.auth.isAuth;
      store.commit('auth/clearSession');
      store.dispatch('auth/_resetAllUserState');
      if (wasAuth) {
        store.dispatch(
          'flash',
          { type: 'info', message: t('auth.session.loggedOutInOtherTab') },
          { root: true }
        );
      }
      return;
    }

    let next;
    try { next = JSON.parse(event.newValue); } catch { return; }
    if (!next || !next.accessToken) return;

    const cur = store.state.auth;
    const userChanged = cur.user && next.user && cur.user.id !== next.user.id;
    if (userChanged) {
      store.dispatch('auth/_resetAllUserState');
    }
    if (cur.accessToken !== next.accessToken || userChanged) {
      store.commit('auth/setSession', next);
    }
  });
}

export default {
  namespaced: true,
  state: () => ({
    accessToken: null,
    refreshToken: null,
    refreshTokenExpiresAt: null,
    user: null,
    isAuth: false,
  }),
  getters: {
    isAdmin: (s) => s.user && s.user.roles && s.user.roles.includes('Administrator'),
    isDoctor: (s) =>
      s.user && s.user.roles && s.user.roles.includes('Doctor'),
    fullName: (s) => (s.user ? s.user.fullName || `${s.user.firstName} ${s.user.lastName}` : ''),
  },
  mutations: {
    setSession(state, payload) {
      state.accessToken = payload.accessToken;
      state.refreshToken = payload.refreshToken;
      state.refreshTokenExpiresAt = payload.refreshTokenExpiresAt;
      state.user = payload.user;
      state.isAuth = true;
      saveSession(payload);
    },
    setUser(state, user) {
      state.user = user;
      if (state.accessToken) {
        saveSession({
          accessToken: state.accessToken,
          refreshToken: state.refreshToken,
          refreshTokenExpiresAt: state.refreshTokenExpiresAt,
          user,
        });
      }
    },
    clearSession(state) {
      state.accessToken = null;
      state.refreshToken = null;
      state.refreshTokenExpiresAt = null;
      state.user = null;
      state.isAuth = false;
      clearSession();
    },
  },
  actions: {
    _resetAllUserState({ commit }) {
      const modules = ['profile', 'notifications', 'analyses', 'patients', 'blog'];
      for (const m of modules) {
        try { commit(`${m}/reset`, null, { root: true }); } catch { /* ignore */ }
      }
    },

    async login({ commit, dispatch }, { email, password }) {
      try {
        const { data } = await authApi.login(email, password);
        await dispatch('_resetAllUserState');
        commit('setSession', data);
        return data;
      } catch (err) {
        const msg =
          err.response?.data?.detail ||
          err.response?.data?.title ||
          t('auth.session.errorGenericLogin');
        dispatch('flash', { type: 'error', message: msg }, { root: true });
        throw err;
      }
    },

    async register({ dispatch }, payload) {
      try {
        await authApi.register(payload);
        dispatch(
          'flash',
          { type: 'success', message: t('auth.signUp.successRegistered') },
          { root: true }
        );
      } catch (err) {
        const msg =
          err.response?.data?.detail ||
          err.response?.data?.title ||
          t('auth.signUp.errorGenericRegister');
        dispatch('flash', { type: 'error', message: msg }, { root: true });
        throw err;
      }
    },

    async refresh({ state, commit }) {
      if (!state.refreshToken) {
        throw new Error('No refresh token available');
      }
      const { data } = await authApi.refresh(state.refreshToken);
      commit('setSession', data);
      return data.accessToken;
    },

    /**
     * Best-effort logout.
     *
     * Hits the server to invalidate the refresh token, but local state is
     * cleared UNCONDITIONALLY at the end — even if the server call fails
     * (because token expired, network down, server unreachable, etc.).
     *
     * IMPORTANT: this used to fall into a recursive loop because client.js's
     * 401-interceptor would call `auth/logout` again whenever refresh failed
     * during a logout attempt. The fix is in client.js: /auth/logout is now
     * excluded from the refresh-retry list, so a 401 just bubbles back here
     * and the catch block does its job.
     */
    async logout({ state, commit, dispatch }) {
      try {
        if (state.refreshToken) {
          await authApi.logout(state.refreshToken);
        }
      } catch {
        // ignore — we still clear local state
      }
      commit('clearSession');
      await dispatch('_resetAllUserState');
    },

    restoreSession(context) {
      const { commit } = context;
      const session = loadSession();
      if (session && session.accessToken) {
        commit('setSession', session);
      }
      bindCrossTabSync(this);
    },

    async fetchMe({ commit }) {
      const { data } = await authApi.me();
      commit('setUser', data);
      return data;
    },
  },
};
