import blogApi from '@/api/blog';

function normalizeListItem(p) {
  if (!p) return p;
  return {
    ...p,
    isLiked: p.likedByMe ?? p.isLiked ?? false,
  };
}

export default {
  namespaced: true,
  state: () => ({
    posts: [],
    total: 0,
    current: null,
    comments: [],
    loading: false,
  }),
  mutations: {
    setLoading(state, v) { state.loading = v; },
    setPosts(state, { items, total }) {
      state.posts = items;
      state.total = total;
    },
    setCurrent(state, post) { state.current = post; },
    setComments(state, comments) { state.comments = comments; },
    prependComment(state, c) { state.comments.unshift(c); },
    toggleLike(state, postId) {
      const idx = state.posts.findIndex((p) => p.id === postId);
      if (idx >= 0) {
        const p = state.posts[idx];
        state.posts[idx] = {
          ...p,
          isLiked: !p.isLiked,
          likesCount: (p.likesCount || 0) + (p.isLiked ? -1 : 1),
        };
      }
      if (state.current && state.current.id === postId) {
        state.current = {
          ...state.current,
          isLiked: !state.current.isLiked,
          likesCount: (state.current.likesCount || 0) + (state.current.isLiked ? -1 : 1),
        };
      }
    },
    reset(state) {
      state.posts = [];
      state.total = 0;
      state.current = null;
      state.comments = [];
      state.loading = false;
    },
  },
  actions: {
    async loadPosts({ commit }, params = {}) {
      commit('setLoading', true);
      try {
        const { data } = await blogApi.list(params);
        const items = (data.items || []).map(normalizeListItem);
        commit('setPosts', { items, total: data.totalCount ?? items.length });
      } finally {
        commit('setLoading', false);
      }
    },
    async loadOne({ commit }, id) {
      const { data } = await blogApi.get(id);
      const norm = normalizeListItem(data);
      commit('setCurrent', norm);
      return norm;
    },
    async loadComments({ commit }, id) {
      const { data } = await blogApi.comments(id, { pageSize: 100 });
      commit('setComments', data.items || data || []);
    },
    async create(_ctx, payload) { return blogApi.create(payload); },
    async like({ commit }, id) {
      commit('toggleLike', id);
      try {
        await blogApi.toggleLike(id);
      } catch (e) {
        commit('toggleLike', id); // revert
        throw e;
      }
    },
    async addComment({ commit }, { postId, content }) {
      const { data } = await blogApi.addComment(postId, content);
      commit('prependComment', data);
      return data;
    },
  },
};
