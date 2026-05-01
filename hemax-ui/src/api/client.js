import axios from 'axios';
import store from '@/store';
import router from '@/router';

const API_BASE = process.env.VUE_APP_API_BASE || '/api';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor — attach JWT
client.interceptors.request.use((config) => {
  const token = store.state.auth.accessToken;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Refresh token deduplication
let isRefreshing = false;
let refreshPromise = null;
let queuedRequests = [];

function flushQueue(error, token = null) {
  queuedRequests.forEach((p) => {
    if (error) p.reject(error);
    else p.resolve(token);
  });
  queuedRequests = [];
}

/**
 * Endpoints that must NEVER trigger refresh-then-retry.
 *
 *   /auth/login    — a 401 here is a real wrong-password (not stale token);
 *                    refreshing is meaningless.
 *   /auth/refresh  — refreshing refresh would be infinite recursion.
 *   /auth/logout   — *** the loop bug ***: logout with expired access token
 *                    returns 401, which used to fire the refresh path, which
 *                    on failure called `auth/logout` again, recursing 5x
 *                    until the browser gave up. Logout is best-effort: a 401
 *                    means the server-side session is gone anyway, which is
 *                    exactly what logout was trying to achieve. Just let the
 *                    error bubble; the store's `logout` action swallows it
 *                    and clears local state.
 */
const NO_REFRESH_PATHS = ['/auth/login', '/auth/refresh', '/auth/logout'];

function isNoRefreshPath(url) {
  if (!url) return false;
  return NO_REFRESH_PATHS.some((p) => url.includes(p));
}

client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response &&
      error.response.status === 401 &&
      !originalRequest._retry &&
      !isNoRefreshPath(originalRequest.url)
    ) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          queuedRequests.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return client(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        refreshPromise = store.dispatch('auth/refresh');
        const newToken = await refreshPromise;
        flushQueue(null, newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return client(originalRequest);
      } catch (refreshErr) {
        flushQueue(refreshErr, null);
        try {
          store.commit('auth/clearSession');
        } catch { /* ignore */ }
        try {
          await store.dispatch('auth/_resetAllUserState');
        } catch { /* ignore */ }
        if (router.currentRoute.value?.path !== '/sign-in') {
          router.push('/sign-in');
        }
        return Promise.reject(refreshErr);
      } finally {
        isRefreshing = false;
        refreshPromise = null;
      }
    }

    return Promise.reject(error);
  }
);

export default client;
