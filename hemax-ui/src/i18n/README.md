# HEMAX i18n — how it works & how to extend

## Architecture

- **No external dependency.** Plain Vue 3 `reactive()` + `inject()`.
- **Two dictionaries:** `uk.json` (source of truth) + `en.json` (mirror).
- **Dot-path keys:** `$t('nav.home')` resolves to `dict.nav.home`.
- **Interpolation:** `$t('userHome.welcome', { name: 'Anna' })` for `"Welcome, {name}!"`.
- **Reactive switch:** `setLocale('en')` re-renders all `$t()` calls instantly.
- **Persistence:** locale saved to `localStorage['hemax-locale']`. Also reflected on `<html lang="...">`.
- **Browser preference fallback:** if no localStorage and browser is `en-*`, defaults to `en`. Otherwise `uk`.
- **Missing-key fallback:** returns the raw key (visible in UI) — easy to spot missing translations.
- **Missing-translation fallback:** if EN is missing a key, falls through to UK.

## Files

```
src/i18n/
├── index.js        ← Plugin + composable + reactive state
├── uk.json         ← Source of truth — add new keys HERE FIRST
├── en.json         ← English mirror — add same key with EN text
└── README.md       ← this
```

## Usage in components

```vue
<!-- Options API -->
<template>
  <h1>{{ $t('nav.home') }}</h1>
  <p>{{ $t('userHome.welcome', { name: user.firstName }) }}</p>
  <p>Current language: {{ $locale }}</p>
</template>

<script>
export default {
  methods: {
    saveProfile() {
      this.$store.dispatch('flash', {
        type: 'success',
        message: this.$t('common.success'),
      });
    },
  },
};
</script>
```

```vue
<!-- Composition API -->
<script setup>
import { inject } from 'vue';
const { t, setLocale, state } = inject('i18n');
</script>

<template>
  <button @click="setLocale('en')">{{ t('locale.en') }}</button>
</template>
```

## Usage in plain JS (constants, utils)

```js
import { t } from '@/i18n';

export function severityLabel(level) {
  return t(`severity.${level}`);
}
```

## Switching language

```js
import { setLocale } from '@/i18n';
setLocale('en');   // instant; persists to localStorage
```

The `<LanguageSwitcher />` component does this for you.

## Adding new strings — workflow

1. **Decide on a namespace.** Existing top-level groups:
   - `common.*` — shared buttons / labels
   - `nav.*`, `header.*`, `footer.*`
   - `auth.*` — login / signup / reset
   - `profile.*` — profile sections
   - `analyses.*` — list view
   - `analysis.*` — submit forms (cbc/chem/risk/neuro/derma sub-namespaces)
   - `results.*` — result display components
   - `severity.*`, `tone.*`, `tier.*`, `direction.*` — model output labels
   - `blog.*`, `faq.*`, `home.*`, `userHome.*`, `patients.*`, `admin.*`
   - `notifications.*`, `validation.*`, `errors.*`

2. **Add the key to `uk.json` FIRST** (source of truth):
   ```json
   "myFeature": {
     "title": "Заголовок",
     "subtitle": "Підзаголовок з {name}"
   }
   ```

3. **Mirror to `en.json` IMMEDIATELY** — even if just a TODO:
   ```json
   "myFeature": {
     "title": "Title",
     "subtitle": "Subtitle with {name}"
   }
   ```

4. **Use it in the template:**
   ```vue
   <h1>{{ $t('myFeature.title') }}</h1>
   <p>{{ $t('myFeature.subtitle', { name: user.name }) }}</p>
   ```

## Don't do these

- ❌ Don't add a key to `en.json` without adding it to `uk.json` — UA is the source.
- ❌ Don't use template literals or string concatenation:
   `$t('greet' + suffix)` → unmaintainable; use full keys.
- ❌ Don't translate user-generated content (analysis results from the analyzer,
   blog post body, user names). Those have their own language plumbing via
   `UserProfile.preferredLanguage` → analyzer `lang` param.

## Sync with UserProfile.preferredLanguage

The user's preferred narrative language (UA/EN for AI-generated analysis
narratives) is stored on the backend as `UserProfile.preferredLanguage`.
The UI locale (this i18n system) is a separate concern.

When a logged-in user changes the UI locale via `<LanguageSwitcher />`:

- localStorage is updated (always).
- The `UserProfile.preferredLanguage` is **optionally** PATCHed to match —
  controlled by the `syncBackend` option in the switcher. This makes new
  analyses come back in the same language the user is reading the UI in.
- Existing analyses keep their original narrative language.

This dual-state design lets:
- Anonymous (logged-out) users still switch UI language.
- Logged-in users have UI language + preferred narrative language sync'd
  by default but separable if needed (e.g. UA UI but EN clinical reports
  for sharing with foreign doctor).
