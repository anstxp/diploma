import { setLocale, getLocale, availableLocales } from '@/i18n';
import profileApi from '@/api/profile';

const STORAGE_KEY = 'hemax-locale';

export default {
  namespaced: true,

  state: () => ({
    syncedAt: null,
    lastError: null,
  }),

  getters: {
    current: () => getLocale(),
    available: () => availableLocales(),
  },

  actions: {
    async setLocale({ rootState, commit }, payload) {
      const locale = typeof payload === 'string' ? payload : payload.locale;
      const syncBackend = typeof payload === 'object'
        ? payload.syncBackend !== false
        : true;

      setLocale(locale);

      if (!syncBackend) return;
      if (!rootState.auth?.isAuth) return;  // anonymous — no profile

      try {
        const { data } = await profileApi.update({ preferredLanguage: locale });
        commit('setSyncedAt', new Date().toISOString());
        commit('setLastError', null);

        if (data) {
          commit('profile/set', data, { root: true });
        }
      } catch (e) {
        const msg = e?.response?.data?.detail || e?.message || 'unknown';
        console.warn('[i18n] backend sync failed:', msg);
        commit('setLastError', msg);
      }
    },

    syncFromProfile({ rootState }) {
      // Local choice present → it wins.
      const hasLocal = typeof localStorage !== 'undefined'
        && !!localStorage.getItem(STORAGE_KEY);
      if (hasLocal) return;

      const profileLang = rootState.profile?.profile?.preferredLanguage;
      if (profileLang === 'uk' || profileLang === 'en') {
        setLocale(profileLang);
      }
    },
  },

  mutations: {
    setSyncedAt(state, ts) {
      state.syncedAt = ts;
    },
    setLastError(state, msg) {
      state.lastError = msg;
    },
  },
};
