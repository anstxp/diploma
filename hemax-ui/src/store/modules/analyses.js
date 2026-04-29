import analysesApi, { ANALYSIS_TYPE_NAME } from '@/api/analyses';
import { t, getLocale } from '@/i18n';

function normalizeSummary(a) {
  if (!a) return a;
  return {
    ...a,
    type: a.typeName || (typeof a.type === 'number' ? ANALYSIS_TYPE_NAME[a.type] : a.type),
    severityLabel: a.severityName || a.severity,
    doctorReviewedAt: a.hasDoctorReview ? (a.doctorReviewedAt || true) : null,
  };
}

function normalizeDetail(a) {
  if (!a) return a;
  let result = {};
  if (a.resultJson) {
    try { result = JSON.parse(a.resultJson); } catch { result = {}; }
  }
  let rawInput = {};
  if (a.rawInputJson) {
    try { rawInput = JSON.parse(a.rawInputJson); } catch { rawInput = {}; }
  }
  return {
    ...a,
    type: a.typeName || (typeof a.type === 'number' ? ANALYSIS_TYPE_NAME[a.type] : a.type),
    severityLabel: a.severityName || a.severity,
    result,
    rawInput,
  };
}

export default {
  namespaced: true,
  state: () => ({
    list: [],
    total: 0,
    current: null,
    loading: false,
  }),
  mutations: {
    setLoading(state, v) { state.loading = v; },
    setList(state, { items, total }) {
      state.list = items;
      state.total = total;
    },
    setCurrent(state, item) { state.current = item; },
    prepend(state, item) {
      state.list.unshift(item);
      state.total += 1;
    },
    reset(state) {
      state.list = [];
      state.total = 0;
      state.current = null;
      state.loading = false;
    },
  },
  actions: {
    async loadList({ commit }, params = {}) {
      commit('setLoading', true);
      try {
        const { data } = await analysesApi.list(params);
        const items = (data.items || []).map(normalizeSummary);
        commit('setList', { items, total: data.totalCount ?? items.length });
      } finally {
        commit('setLoading', false);
      }
    },
    async loadMy({ dispatch }, params = {}) { return dispatch('loadList', params); },
    async loadAll({ dispatch }, params = {}) { return dispatch('loadList', params); },

    async remove(_ctx, id) {
      await analysesApi.delete(id);
    },
    async loadOne({ commit }, payload) {
      const id   = typeof payload === 'string' ? payload : payload?.id;
      const lang = (typeof payload === 'object' && payload?.language)
                     ? payload.language
                     : getLocale() || 'uk';

      commit('setLoading', true);
      try {
        const { data } = await analysesApi.get(id, lang);
        commit('setCurrent', normalizeDetail(data));
      } finally {
        commit('setLoading', false);
      }
    },
    async submit({ commit, dispatch }, { kind, payload, mergeRecentLabs = false, language }) {
      const lang = language || getLocale() || 'uk';

      let res;
      if (kind === 'derma') {
        if (payload instanceof FormData) {
          const file = payload.get('image') || payload.get('file');
          const formLang = payload.get('language') || lang;
          const extras = {};
          for (const [k, v] of payload.entries()) {
            if (!['image', 'file', 'language'].includes(k)) extras[k] = v;
          }
          res = await analysesApi.submitDerma(file, formLang, extras);
        } else {
          const file = payload.file || payload.image;
          const formLang = payload.language || lang;
          const extras = { ...payload };
          delete extras.file;
          delete extras.image;
          delete extras.language;
          res = await analysesApi.submitDerma(file, formLang, extras);
        }
      } else {
        res = await analysesApi.submit(kind, payload, lang, mergeRecentLabs);
      }
      const norm = normalizeDetail(res.data);
      commit('prepend', normalizeSummary(res.data));
      dispatch('flash', { type: 'success', message: t('analysis.flashSubmitted') }, { root: true });
      return norm;
    },
  },
};
