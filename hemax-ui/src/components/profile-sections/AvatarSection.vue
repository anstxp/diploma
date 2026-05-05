<template>
  <section class="section avatar-section">
    <div class="avatar-row">
      <div class="avatar-display">
        <img v-if="profile.avatarUrl" :src="profile.avatarUrl" :alt="profile.firstName" />
        <div v-else class="avatar-placeholder">
          {{ initials }}
        </div>
      </div>
      <div class="avatar-controls">
        <h2><i class="fa-solid fa-camera"></i> {{ $t('profile.avatar.title') }}</h2>
        <p class="section-hint">{{ $t('profile.avatar.hint') }}</p>
        <div class="avatar-actions">
          <label class="btn primary file-btn">
            <i class="fa-solid fa-upload"></i>
            {{ uploading ? $t('profile.avatar.uploading') : $t('profile.avatar.uploadButton') }}
            <input type="file" accept="image/jpeg,image/png,image/webp"
                   @change="onAvatarSelected" :disabled="uploading" />
          </label>
          <button v-if="profile.avatarUrl" type="button" class="btn ghost"
                  @click="onRemoveAvatar" :disabled="uploading">
            {{ $t('profile.avatar.removeButton') }}
          </button>
        </div>
      </div>
    </div>
  </section>
</template>

<script>
import profileApi from "@/api/profile";
import {
  validateAvatar, checkImageMagicBytes, extractApiError,
} from "@/utils/validation";

export default {
  name: "AvatarSection",
  props: {
    profile: { type: Object, required: true },
  },
  emits: ["changed"],
  data() {
    return { uploading: false };
  },
  computed: {
    initials() {
      const f = (this.profile.firstName || "").trim();
      const l = (this.profile.lastName  || "").trim();
      return ((f[0] || "") + (l[0] || "")).toUpperCase() || "?";
    },
  },
  methods: {
    async onAvatarSelected(ev) {
      const file = ev.target.files?.[0];
      if (!file) return;
      ev.target.value = "";

      const err = validateAvatar(file);
      if (err) {
        this.$store.dispatch("flash", { type: "error", message: err });
        return;
      }
      if (!(await checkImageMagicBytes(file))) {
        this.$store.dispatch("flash", {
          type: "error",
          message: this.$t('profile.avatar.errorBadImage'),
        });
        return;
      }

      this.uploading = true;
      try {
        await profileApi.uploadAvatar(file);
        this.$emit("changed");
        this.$store.dispatch("flash", { type: "success", message: this.$t('profile.avatar.successUpload') });
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: extractApiError(e, this.$t('profile.avatar.errorUpload')),
        });
      } finally {
        this.uploading = false;
      }
    },

    async onRemoveAvatar() {
      if (!confirm(this.$t('profile.avatar.removeConfirm'))) return;
      this.uploading = true;
      try {
        await profileApi.removeAvatar();
        this.$emit("changed");
        this.$store.dispatch("flash", { type: "success", message: this.$t('profile.avatar.successRemove') });
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('profile.avatar.errorRemove'),
        });
      } finally {
        this.uploading = false;
      }
    },
  },
};
</script>
