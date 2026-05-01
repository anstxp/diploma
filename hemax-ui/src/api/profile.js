import client from './client';

export default {
  get() {
    return client.get('/profile');
  },

  getByUserId(userId) {
    return client.get(`/profile/${userId}`);
  },

  update(data) {
    return client.put('/profile', data);
  },

  uploadAvatar(file) {
    const fd = new FormData();
    fd.append('file', file);
    return client.post('/users/me/avatar', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },

  /** Remove current avatar. */
  removeAvatar() {
    return client.delete('/users/me/avatar');
  },
};
