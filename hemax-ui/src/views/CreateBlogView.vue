<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <button class="link-back" @click="$router.back()">
      <i class="fa-solid fa-arrow-left"></i> {{ $t('blog.create.back') }}
    </button>

    <h1 class="page-title">{{ $t('blog.create.pageTitle') }}</h1>

    <form class="create-form" @submit.prevent="onSubmit">
      <div class="form-row cover-row">
        <span>{{ $t('blog.create.coverLabel') }} <small>{{ $t('blog.create.coverSubtitle') }}</small></span>

        <div v-if="coverPreview" class="cover-preview">
          <img :src="coverPreview" :alt="$t('blog.create.coverPreviewAlt')" />
          <div class="cover-actions">
            <label class="btn-outline btn-small file-btn">
              <i class="fa-solid fa-arrows-rotate"></i> {{ $t('blog.create.coverReplaceButton') }}
              <input
                type="file"
                accept="image/jpeg,image/png,image/webp"
                @change="onCoverSelected"
              />
            </label>
            <button type="button" class="btn-outline btn-small danger" @click="clearCover">
              <i class="fa-solid fa-xmark"></i> {{ $t('blog.create.coverClearButton') }}
            </button>
          </div>
        </div>

        <label v-else class="cover-empty file-btn">
          <i class="fa-solid fa-image"></i>
          <span>{{ $t('blog.create.coverEmptyPrompt') }}</span>
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            @change="onCoverSelected"
          />
        </label>

        <small v-if="coverError" class="error-message">{{ coverError }}</small>
      </div>

      <div class="form-row">
        <span>{{ $t('blog.create.titleLabel') }}</span>
        <input v-model="form.title" type="text" class="box" maxlength="300" required />
      </div>

      <div class="form-row">
        <span>{{ $t('blog.create.tagsLabel') }}</span>
        <input
          v-model="form.tags"
          type="text"
          class="box"
          :placeholder="$t('blog.create.tagsPlaceholder')"
        />
      </div>

      <div class="form-row">
        <span>{{ $t('blog.create.contentLabel') }}</span>
        <textarea v-model="form.content" class="box" rows="14" required></textarea>
      </div>

      <div class="form-row">
        <label class="checkbox">
          <input type="checkbox" v-model="form.isPublished" />
          {{ $t('blog.create.publishCheckbox') }}
        </label>
      </div>

      <div class="actions">
        <button type="submit" class="btn" :disabled="loading">
          {{ submitLabel }}
        </button>
      </div>
    </form>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import blogApi from "@/api/blog";

const MAX_COVER_BYTES = 10 * 1024 * 1024; // 10 MB
const ALLOWED_COVER_TYPES = ["image/jpeg", "image/png", "image/webp"];

export default {
  name: "CreateBlogView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent },
  data() {
    return {
      loading: false,
      stage: null, // 'creating' | 'uploading-cover'
      form: { title: "", tags: "", content: "", isPublished: true },
      coverFile: null,
      coverPreview: null,
      coverError: null,
    };
  },
  computed: {
    submitLabel() {
      if (!this.loading) return this.$t('blog.create.submitLabelPublish');
      if (this.stage === "creating") return this.$t('blog.create.submitLabelCreating');
      if (this.stage === "uploading-cover") return this.$t('blog.create.submitLabelUploading');
      return this.$t('blog.create.submitLabelSaving');
    },
  },
  beforeUnmount() {
    // Free memory used by the preview blob URL
    if (this.coverPreview && this.coverPreview.startsWith("blob:")) {
      URL.revokeObjectURL(this.coverPreview);
    }
  },
  methods: {
    onCoverSelected(ev) {
      const file = ev.target.files?.[0];
      ev.target.value = ""; // allow picking the same file again later
      if (!file) return;

      if (!ALLOWED_COVER_TYPES.includes(file.type)) {
        this.coverError = this.$t('blog.create.coverFormatError');
        return;
      }
      if (file.size > MAX_COVER_BYTES) {
        this.coverError = this.$t('blog.create.coverSizeError');
        return;
      }

      this.coverError = null;
      if (this.coverPreview && this.coverPreview.startsWith("blob:")) {
        URL.revokeObjectURL(this.coverPreview);
      }
      this.coverFile = file;
      this.coverPreview = URL.createObjectURL(file);
    },

    clearCover() {
      if (this.coverPreview && this.coverPreview.startsWith("blob:")) {
        URL.revokeObjectURL(this.coverPreview);
      }
      this.coverFile = null;
      this.coverPreview = null;
      this.coverError = null;
    },

    async onSubmit() {
      this.loading = true;
      try {
        // Step 1 — create the post itself
        this.stage = "creating";
        const payload = {
          title: this.form.title.trim(),
          content: this.form.content.trim(),
          tags: this.form.tags.split(",").map((s) => s.trim()).filter(Boolean),
          isPublished: this.form.isPublished,
        };
        const { data } = await this.$store.dispatch("blog/create", payload);
        const newId = data.id;

        if (this.coverFile) {
          this.stage = "uploading-cover";
          try {
            await blogApi.uploadCover(newId, this.coverFile);
          } catch (e) {
            this.$store.dispatch("flash", {
              type: "warning",
              message: this.$t('blog.create.coverSecondaryWarning'),
            });
            this.$router.push(`/blog/${newId}`);
            return;
          }
        }

        this.$store.dispatch("flash", {
          type: "success",
          message: this.$t('blog.create.createSuccess'),
        });
        this.$router.push(`/blog/${newId}`);
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('blog.create.createError'),
        });
      } finally {
        this.loading = false;
        this.stage = null;
      }
    },
  },
};
</script>

<style scoped lang="scss">
.link-back {
  background: transparent;
  color: var(--purple);
  font-size: 1.3rem;
  cursor: pointer;
  margin-bottom: 1.5rem;
  font-family: inherit;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  text-transform: none;

  &:hover { text-decoration: underline; }
}

.create-form {
  max-width: 80rem;
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 2rem;

  .form-row { margin-bottom: 1.2rem; }

  .form-row > span {
    display: block;
    font-size: 1.3rem;
    color: var(--black);
    margin-bottom: 0.4rem;
    text-transform: lowercase;

    small {
      color: var(--light-color);
      font-size: 1.1rem;
      margin-left: 0.4rem;
    }
  }

  .box {
    width: 100%;
    padding: 0.9rem 1.2rem;
    font-size: 1.4rem;
    border: var(--border);
    border-radius: 0.5rem;
    text-transform: none;
    resize: vertical;

    &:focus { border-color: var(--purple); }
  }

  .checkbox {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    font-size: 1.4rem;
    cursor: pointer;
    text-transform: none;
    color: var(--black);

    input[type="checkbox"] {
      accent-color: var(--purple);
      width: 1.6rem;
      height: 1.6rem;
    }
  }

  .actions {
    margin-top: 1.5rem;
    text-align: right;
  }
}

.cover-row {
  .file-btn input[type="file"] { display: none; }

  .cover-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    padding: 3.5rem 2rem;
    border: 2px dashed rgba(65, 90, 119, 0.3);
    border-radius: 0.6rem;
    color: var(--light-color);
    cursor: pointer;
    transition: border-color 0.15s, color 0.15s;
    text-transform: none;
    font-size: 1.3rem;

    i { font-size: 2.4rem; color: var(--purple); }

    &:hover { border-color: var(--purple); color: var(--purple); }
  }

  .cover-preview {
    position: relative;
    border-radius: 0.6rem;
    overflow: hidden;
    border: var(--border);
    background: var(--bg);

    img {
      width: 100%;
      max-height: 36rem;
      object-fit: cover;
      display: block;
    }

    .cover-actions {
      position: absolute;
      top: 1rem;
      right: 1rem;
      display: flex;
      gap: 0.6rem;

      .file-btn,
      button {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        padding: 0.6rem 1rem;
        font-size: 1.2rem;
        background: rgba(255, 255, 255, 0.95);
        border: var(--border);
        border-radius: 0.4rem;
        color: var(--black);
        cursor: pointer;
        text-transform: lowercase;
        font-family: inherit;

        &:hover { background: white; }
        &.danger { color: #a32d2d; }
        &.danger:hover { background: rgba(226, 75, 74, 0.1); }
      }
    }
  }

  .error-message {
    display: block;
    color: #a32d2d;
    font-size: 1.2rem;
    margin-top: 0.6rem;
    text-transform: none;
  }
}
</style>
