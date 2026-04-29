import profileApi from '@/api/profile';
import { extractApiError } from '@/utils/validation';
import { t } from '@/i18n';

const initialState = () => ({
  profile: null,
  loading: false,
  error: null,
});

const state = initialState;

const mutations = {
  set(state, profile) { state.profile = profile; },
  setLoading(state, v) { state.loading = v; },
  setError(state, e) { state.error = e; },
  reset(state) {
    Object.assign(state, initialState());
  },
};

const getters = {
  age(state) {
    return state.profile?.age ?? null;
  },
  /** Sex value as expected by analysis forms. */
  sex(state) {
    return state.profile?.sex ?? null;
  },
  hasMedicalData(state) {
    const p = state.profile;
    if (!p) return false;
    return !!(p.heightCm || p.weightKg || p.chronicDiseases ||
              p.allergies || p.currentMedications);
  },
};

const actions = {
  async fetch({ commit }) {
    commit('setLoading', true);
    commit('setError', null);
    try {
      const { data } = await profileApi.get();
      commit('set', data);
      return data;
    } catch (e) {
      commit('setError', e.message);
      throw e;
    } finally {
      commit('setLoading', false);
    }
  },

  async update({ commit, dispatch }, payload) {
    commit('setLoading', true);
    try {
      const { data } = await profileApi.update(payload);
      commit('set', data);
      dispatch('flash', {
        type: 'success', message: t('profile.successUpdated'),
      }, { root: true });
      return data;
    } catch (e) {
      const msg = extractApiError(e, e.message || t('profile.errorUpdate'));
      dispatch('flash', { type: 'error', message: msg }, { root: true });
      throw e;
    } finally {
      commit('setLoading', false);
    }
  },
};

export default {
  namespaced: true,
  state, mutations, getters, actions,
};
