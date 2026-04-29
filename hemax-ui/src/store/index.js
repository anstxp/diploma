import { createStore } from 'vuex';
import auth from './modules/auth';
import analyses from './modules/analyses';
import patients from './modules/patients';
import blog from './modules/blog';
import notifications from './modules/notifications';
import profile from './modules/profile';

export default createStore({
  state: {
    flash: null,
    search: '',
  },
  mutations: {
    setFlash(state, payload) {
      state.flash = payload;
    },
    clearFlash(state) {
      state.flash = null;
    },
    searchInput(state, value) {
      state.search = value;
    },
  },
  actions: {
    flash({ commit }, payload) {
      commit('setFlash', payload);
      setTimeout(() => commit('clearFlash'), 3500);
    },
  },
  modules: {
    auth,
    analyses,
    patients,
    blog,
    notifications,
    profile,
  },
});
