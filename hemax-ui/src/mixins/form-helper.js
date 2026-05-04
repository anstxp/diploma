import { t } from '@/i18n';

export default {
  methods: {
    validateEmail(email) {
      if (!email) return t('validation.email.required');
      const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!re.test(email)) return t('validation.email.invalid');
      return "";
    },
    validatePassword(password) {
      if (!password) return t('validation.password.required');
      if (password.length < 8) return t('validation.password.minLength');
      if (!/[A-Z]/.test(password)) return t('validation.password.needsUpper');
      if (!/[a-z]/.test(password)) return t('validation.password.needsLower');
      if (!/[0-9]/.test(password)) return t('validation.password.needsDigit');
      return "";
    },
    validateRequired(value, fieldName) {
      if (!value || (typeof value === "string" && !value.trim())) {
        const label = fieldName || t('validation.name.defaultLabel');
        return t('validation.name.required', { label });
      }
      return "";
    },
  },
};
