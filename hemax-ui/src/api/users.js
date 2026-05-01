import client from './client';

export const usersApi = {
  me() {
    return client.get('/auth/me');
  },
  updateProfile(payload) {
    // Sex enum: Unknown=0, Male=1, Female=2
    const sexMap = { Unknown: 0, Male: 1, Female: 2 };
    let sexValue = payload.sex;
    if (typeof sexValue === 'string') {
      sexValue = sexMap[sexValue] ?? 0;
    }
    return client.put('/users/me/profile', {
      firstName: payload.firstName,
      lastName: payload.lastName,
      dateOfBirth: payload.dateOfBirth || null,
      sex: sexValue,
    });
  },
  uploadAvatar(file) {
    const fd = new FormData();
    fd.append('file', file);
    return client.post('/users/me/avatar', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  changePassword(currentPassword, newPassword) {
    return client.post('/auth/change-password', { currentPassword, newPassword });
  },
  deleteAccount() {
    return client.delete('/profile');
  },
};

export const notificationsApi = {
  list(params = {}) {
    return client.get('/notifications', { params });
  },
  unreadCount() {
    return client.get('/notifications/unread-count');
  },
  markRead(id) {
    return client.patch(`/notifications/${id}/read`);
  },
  markAllRead() {
    return client.post('/notifications/mark-all-read');
  },
};

export const adminApi = {
  listUsers(params = {}) {
    return client.get('/admin/users', { params });
  },
  setBanned(userId, banned, reason = '') {
    return client.post(`/admin/users/${userId}/ban`, { banned, reason });
  },
  banUser(userId, reason) {
    return this.setBanned(userId, true, reason);
  },
  unbanUser(userId) {
    return this.setBanned(userId, false, '');
  },
  changeRole(userId, role) {
    return client.post(`/admin/users/${userId}/role`, { role });
  },
  auditLog(params = {}) {
    return client.get('/admin/audit-log', { params });
  },
  encryptionTest() {
    return client.get('/admin/encryption/test');
  },
  encryptionInfo() {
    return client.get('/admin/encryption/info');
  },
};
