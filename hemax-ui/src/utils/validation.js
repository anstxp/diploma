import { t } from '@/i18n';

export const IMAGE_MAX_BYTES = 10 * 1024 * 1024;   // 10 MB
export const AVATAR_MAX_BYTES = 5 * 1024 * 1024;   // 5 MB
export const PDF_MAX_BYTES = 25 * 1024 * 1024;     // 25 MB

export const IMAGE_MIME = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp'];
export const IMAGE_EXT = ['.jpg', '.jpeg', '.png', '.webp'];

export const PDF_MIME = ['application/pdf'];
export const PDF_EXT = ['.pdf'];

function fileExtension(name) {
  if (!name) return '';
  const i = name.lastIndexOf('.');
  return i === -1 ? '' : name.slice(i).toLowerCase();
}

export function validateImage(file, maxBytes = IMAGE_MAX_BYTES) {
  if (!file) return t('validation.file.notSelected');
  if (!IMAGE_MIME.includes(file.type)) {
    return t('validation.file.imageFormatsAllowed', {
      type: file.type || t('validation.file.unknownType'),
    });
  }
  if (!IMAGE_EXT.includes(fileExtension(file.name))) {
    return t('validation.file.extensionMismatch');
  }
  if (file.size === 0) return t('validation.file.empty');
  if (file.size > maxBytes) {
    return t('validation.file.tooLarge', { max: Math.floor(maxBytes / 1024 / 1024) });
  }
  return null;
}

export function validateAvatar(file) {
  return validateImage(file, AVATAR_MAX_BYTES);
}

export function validatePdf(file) {
  if (!file) return t('validation.file.notSelected');
  if (!PDF_MIME.includes(file.type)) {
    return t('validation.file.expectedPdf', {
      type: file.type || t('validation.file.unknownType'),
    });
  }
  if (!PDF_EXT.includes(fileExtension(file.name))) {
    return t('validation.file.pdfExtensionRequired');
  }
  if (file.size === 0) return t('validation.file.empty');
  if (file.size > PDF_MAX_BYTES) {
    return t('validation.file.tooLarge', { max: PDF_MAX_BYTES / 1024 / 1024 });
  }
  return null;
}

export async function checkImageMagicBytes(file) {
  if (!file) return false;
  const slice = file.slice(0, 12);
  const buf = await slice.arrayBuffer();
  const b = new Uint8Array(buf);
  if (b.length < 4) return false;

  // JPEG
  if (b[0] === 0xff && b[1] === 0xd8 && b[2] === 0xff) return true;
  // PNG
  if (b.length >= 8 &&
      b[0] === 0x89 && b[1] === 0x50 && b[2] === 0x4e && b[3] === 0x47 &&
      b[4] === 0x0d && b[5] === 0x0a && b[6] === 0x1a && b[7] === 0x0a) return true;
  // WebP — "RIFF" .... "WEBP"
  if (b.length >= 12 &&
      b[0] === 0x52 && b[1] === 0x49 && b[2] === 0x46 && b[3] === 0x46 &&
      b[8] === 0x57 && b[9] === 0x45 && b[10] === 0x42 && b[11] === 0x50) return true;

  return false;
}

export async function checkPdfMagicBytes(file) {
  if (!file) return false;
  const slice = file.slice(0, 5);
  const buf = await slice.arrayBuffer();
  const b = new Uint8Array(buf);
  // "%PDF-"
  return b.length >= 5 &&
         b[0] === 0x25 && b[1] === 0x50 && b[2] === 0x44 && b[3] === 0x46 && b[4] === 0x2d;
}

export function normalizePhone(raw) {
  if (!raw) return '';
  let s = String(raw).trim();
  let result = '';
  let hadPlus = false;
  for (const ch of s) {
    if (ch === '+' && result.length === 0 && !hadPlus) {
      result += '+';
      hadPlus = true;
    } else if (ch >= '0' && ch <= '9') {
      result += ch;
    }
  }
  return result;
}

export function validatePhone(phone) {
  if (!phone || !phone.trim()) return t('validation.phone.required');
  if (!/^[+\d\s\-()]{6,40}$/.test(phone.trim())) {
    return t('validation.phone.invalidChars');
  }
  const digits = normalizePhone(phone).replace(/^\+/, '');
  if (digits.length < 6) return t('validation.phone.tooShort');
  return null;
}

const NAME_RE = /^[\p{L}\p{M}\s'-]+$/u;

export function validateName(value, { required = true, min = 1, max = 80, label } = {}) {
  const v = (value || '').trim();
  const resolvedLabel = label || t('validation.name.defaultLabel');

  if (!v) return required ? t('validation.name.required', { label: resolvedLabel }) : null;
  if (v.length < min) return t('validation.name.minLength', { label: resolvedLabel, min });
  if (v.length > max) return t('validation.name.tooLong', { label: resolvedLabel, max });
  if (!NAME_RE.test(v)) return t('validation.name.invalidChars', { label: resolvedLabel });
  return null;
}

export function validateDateOfBirth(dateStr, { minAge = 13 } = {}) {
  if (!dateStr) return t('validation.dob.required');

  const dob = new Date(dateStr);
  if (Number.isNaN(dob.getTime())) return t('validation.dob.invalid');

  const now = new Date();
  // Strip time portion for fair comparison
  const dobDay = new Date(dob.getFullYear(), dob.getMonth(), dob.getDate());
  const today  = new Date(now.getFullYear(), now.getMonth(), now.getDate());

  if (dobDay >= today) return t('validation.dob.notInFuture');

  // Compute age in completed years
  let age = today.getFullYear() - dobDay.getFullYear();
  const beforeBirthdayThisYear =
    today.getMonth() < dobDay.getMonth() ||
    (today.getMonth() === dobDay.getMonth() && today.getDate() < dobDay.getDate());
  if (beforeBirthdayThisYear) age -= 1;

  if (age < minAge) {
    return t('validation.dob.minAge', { minAge, age });
  }
  if (age > 130) {
    return t('validation.dob.tooOld');
  }
  return null;
}

export function validateEmail(email) {
  if (!email || !email.trim()) return t('validation.email.required');
  const v = email.trim();
  if (v.length > 256) return t('validation.email.tooLong');
  // Practical RFC subset
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)) return t('validation.email.invalid');
  return null;
}

export function validatePassword(pwd) {
  if (!pwd) return t('validation.password.required');
  if (pwd.length < 8) return t('validation.password.minLength');
  if (pwd.length > 128) return t('validation.password.maxLength');
  if (!/[A-Z]/.test(pwd)) return t('validation.password.needsUpper');
  if (!/[a-z]/.test(pwd)) return t('validation.password.needsLower');
  if (!/[0-9]/.test(pwd)) return t('validation.password.needsDigit');
  return null;
}

export function extractApiError(err, fallback) {
  const resolvedFallback = fallback || t('validation.api.fallback');
  if (!err) return resolvedFallback;
  const data = err.response?.data;
  if (!data) return err.message || resolvedFallback;

  if (data.code === 'PHONE_TAKEN') {
    return t('validation.api.phoneTaken');
  }
  if (data.code === 'INVALID_FILE') {
    return data.title || t('validation.api.invalidFile');
  }
  if (data.code === 'PHONE_REQUIRED') {
    return t('validation.api.phoneRequired');
  }

  if (data.errors) {
    if (Array.isArray(data.errors)) {
      const first = data.errors[0];
      if (first?.errorMessage) return first.errorMessage;
    } else if (typeof data.errors === 'object') {
      const first = Object.values(data.errors).flat()[0];
      if (typeof first === 'string') return first;
    }
  }

  return data.detail || data.title || data.message || resolvedFallback;
}
