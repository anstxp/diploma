import client from './client';

export const usersApi = {
  // GET /auth/me returns the current user profile
  me() {
    return client.get('/auth/me');
  },
  // PUT /api/users/me/profile { firstName, lastName, dateOfBirth, sex }
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
  // password change goes through /auth/change-password (not /users/...)
  changePassword(currentPassword, newPassword) {
    return client.post('/auth/change-password', { currentPassword, newPassword });
  },
};

export const notificationsApi = {
  list(params = {}) {
    return client.get('/notifications', { params });
  },
  unreadCount() {
    return client.get('/notifications/unread-count');
  },
  // Backend: PATCH /api/notifications/{id}/read   (NOT POST — that returns 405)
  markRead(id) {
    return client.patch(`/notifications/${id}/read`);
  },
  // Backend: POST /api/notifications/mark-all-read  (NOT /read-all)
  markAllRead() {
    return client.post('/notifications/mark-all-read');
  },
};

export const adminApi = {
  listUsers(params = {}) {
    return client.get('/admin/users', { params });
  },
  // unified ban/unban endpoint: { banned: true|false, reason }
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
