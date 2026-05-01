import client from './client';

export default {
  list(params = {}) {
    return client.get('/blog', { params });
  },
  get(id) {
    return client.get(`/blog/${id}`);
  },
  create(payload) {
    return client.post('/blog', {
      title: payload.title,
      content: payload.content,
      tags: Array.isArray(payload.tags) ? payload.tags : [],
    });
  },
  update(id, payload) {
    return client.put(`/blog/${id}`, {
      title: payload.title,
      content: payload.content,
      tags: Array.isArray(payload.tags) ? payload.tags : [],
    });
  },
  delete(id) {
    return client.delete(`/blog/${id}`);
  },
  toggleLike(id) {
    return client.post(`/blog/${id}/like`);
  },

  uploadCover(id, file) {
    const fd = new FormData();
    fd.append('image', file);
    return client.post(`/blog/${id}/cover`, fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  removeCover(id) {
    return client.delete(`/blog/${id}/cover`);
  },

  comments(id, params = {}) {
    return client.get(`/blog/${id}/comments`, { params });
  },
  addComment(id, content) {
    return client.post(`/blog/${id}/comments`, { content });
  },
  deleteComment(commentId) {
    return client.delete(`/blog/comments/${commentId}`);
  },
  // admin only
  listDeleted(params = {}) {
    return client.get('/blog/deleted', { params });
  },
  recover(id) {
    return client.post(`/blog/${id}/recover`);
  },
};
