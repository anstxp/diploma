import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import store from './store';
import i18n from '@/i18n';

import '@/components/analysis-components/results/shared/analysisResult.scss';

import i18nStoreModule from '@/store/modules/i18n';
store.registerModule('i18n', i18nStoreModule);

store.subscribe((mutation) => {
  if (mutation.type === 'profile/set' && mutation.payload) {
    store.dispatch('i18n/syncFromProfile');
  }
});

store.dispatch('auth/restoreSession')
  .finally(() => {
    createApp(App).use(store).use(router).use(i18n).mount('#app');
  });
