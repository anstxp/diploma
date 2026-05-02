<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <button class="link-back" @click="$router.push('/blog')">
      <i class="fa-solid fa-arrow-left"></i> {{ $t('blog.details.back') }}
    </button>

    <div v-if="loading" class="loader">{{ $t('blog.details.loading') }}</div>

    <article v-else-if="post" class="post-full">
      <!-- Cover image -->
      <div v-if="post.coverImageUrl" class="cover-image">
        <img :src="post.coverImageUrl" :alt="post.title" />
      </div>

      <div class="post-meta">
        <span><i class="fa-solid fa-user"></i> {{ post.authorName }}</span>
        <span><i class="fa-solid fa-clock"></i> {{ formatDate(post.createdAt) }}</span>
      </div>

      <div class="post-header">
        <h1>{{ post.title }}</h1>
        <div v-if="canEdit" class="post-controls">
          <button
            class="control-btn"
            @click="onUploadCoverClick"
            :disabled="uploadingCover"
            :title="post.coverImageUrl
              ? $t('blog.details.controls.replaceCoverTooltip')
              : $t('blog.details.controls.uploadCoverTooltip')"
          >
            <i class="fa-solid fa-image"></i>
            {{ uploadingCover
                 ? $t('blog.details.controls.uploadingShort')
                 : (post.coverImageUrl
                    ? $t('blog.details.controls.replaceLabel')
                    : $t('blog.details.controls.coverLabel')) }}
          </button>
          <button
            v-if="post.coverImageUrl"
            class="control-btn"
            @click="onRemoveCover"
            :title="$t('blog.details.controls.removeCoverTooltip')"
          >
            <i class="fa-solid fa-image-portrait"></i>
            {{ $t('blog.details.controls.removeCoverButton') }}
          </button>
          <button
            class="control-btn danger"
            @click="onDeletePost"
            :title="$t('blog.details.controls.deletePostTooltip')"
          >
            <i class="fa-solid fa-trash"></i> {{ $t('blog.details.controls.deletePostButton') }}
          </button>
          <input ref="coverFileInput" type="file" accept="image/jpeg,image/png,image/webp"
                 style="display:none" @change="onCoverFileSelected" />
        </div>
      </div>

      <div class="tags" v-if="tagsList.length">
        <span v-for="t in tagsList" :key="t" class="tag">#{{ t }}</span>
      </div>

      <div class="content">{{ post.content }}</div>

      <div class="post-actions">
        <button class="like-btn" :class="{ liked: post.isLiked }" @click="toggleLike">
          <i class="fa-solid fa-heart"></i> {{ post.likesCount || 0 }}
        </button>
      </div>

      <CommentList :post-id="post.id" :comments="comments" />
    </article>

    <div v-else class="empty-state">
      <i class="fa-solid fa-circle-exclamation"></i>
      <p>{{ $t('blog.details.notFound') }}</p>
    </div>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import CommentList from "@/components/blog-components/comment-list.vue";
import blogApi from "@/api/blog";

export default {
  name: "BlogPostDetailsView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent, CommentList },
  data() { return { loading: false, uploadingCover: false }; },
  computed: {
    post() { return this.$store.state.blog.current; },
    comments() { return this.$store.state.blog.comments; },
    user() { return this.$store.state.auth.user; },
    canEdit() {
      if (!this.post || !this.user) return false;
      const isAuthor = this.user.id === this.post.authorId;
      const isAdmin  = (this.user.roles || []).some(r => /admin/i.test(r));
      return isAuthor || isAdmin;
    },
    tagsList() {
      const t = this.post?.tags;
      if (!t) return [];
      return Array.isArray(t) ? t : String(t).split(",").map((s) => s.trim()).filter(Boolean);
    },
  },
  async mounted() {
    this.loading = true;
    try {
      await this.$store.dispatch("blog/loadOne", this.$route.params.id);
      await this.$store.dispatch("blog/loadComments", this.$route.params.id);
    } finally {
      this.loading = false;
    }
  },
  methods: {
    formatDate(iso) {
      if (!iso) return "";
      const lang = this.$locale === "en" ? "en-US" : "uk-UA";
      return new Date(iso).toLocaleDateString(lang, { day: "numeric", month: "long", year: "numeric" });
    },
    async toggleLike() {
      if (!this.$store.state.auth.isAuth) return this.$router.push("/sign-in");
      try {
        await this.$store.dispatch("blog/like", this.post.id);
      } catch {
        this.$store.dispatch("flash", { type: "error", message: this.$t('blog.details.likeError') });
      }
    },

    onUploadCoverClick() {
      this.$refs.coverFileInput.click();
    },
    async onCoverFileSelected(e) {
      const file = e.target.files?.[0];
      if (!file) return;
      if (file.size > 10 * 1024 * 1024) {
        this.$store.dispatch("flash", {
          type: "error",
          message: this.$t('blog.details.coverTooLarge'),
        });
        return;
      }
      this.uploadingCover = true;
      try {
        await blogApi.uploadCover(this.post.id, file);
        // Reload post to get fresh SAS URL
        await this.$store.dispatch("blog/loadOne", this.post.id);
        this.$store.dispatch("flash", {
          type: "success",
          message: this.$t('blog.details.coverUploadSuccess'),
        });
      } catch (err) {
        this.$store.dispatch("flash", {
          type: "error",
          message: err.response?.data?.detail || this.$t('blog.details.coverUploadError'),
        });
      } finally {
        this.uploadingCover = false;
        e.target.value = "";  // allow re-selecting same file
      }
    },
    async onRemoveCover() {
      if (!confirm(this.$t('blog.details.removeCoverConfirm'))) return;
      try {
        await blogApi.removeCover(this.post.id);
        await this.$store.dispatch("blog/loadOne", this.post.id);
        this.$store.dispatch("flash", {
          type: "success",
          message: this.$t('blog.details.removeCoverSuccess'),
        });
      } catch (err) {
        this.$store.dispatch("flash", {
          type: "error",
          message: err.response?.data?.detail || this.$t('blog.details.removeCoverError'),
        });
      }
    },
    async onDeletePost() {
      if (!confirm(this.$t('blog.details.deletePostConfirm'))) return;
      try {
        await blogApi.delete(this.post.id);
        this.$store.dispatch("flash", {
          type: "success",
          message: this.$t('blog.details.deletePostSuccess'),
        });
        this.$router.push("/blog");
      } catch (err) {
        this.$store.dispatch("flash", {
          type: "error",
          message: err.response?.data?.detail || this.$t('blog.details.deletePostError'),
        });
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

.post-full {
  max-width: 80rem;
  margin: 0 auto;
  background: white;
  border: var(--border);
  border-radius: var(--radius);
  padding: 3rem;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  min-width: 0;

  .cover-image {
    margin: -3rem -3rem 2rem;
    border-radius: var(--radius) var(--radius) 0 0;
    overflow: hidden;
    aspect-ratio: 16 / 7;
    background: var(--purple-soft);

    img { width: 100%; height: 100%; object-fit: cover; display: block; }
  }

  .post-meta {
    display: flex;
    gap: 1.5rem;
    flex-wrap: wrap;
    font-size: 1.2rem;
    color: var(--light-color);
    margin-bottom: 1rem;
    text-transform: none;

    i { color: var(--purple); margin-right: 0.4rem; }
  }

  .post-header {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
    align-items: flex-start;
    flex-wrap: wrap;
    margin-bottom: 1.5rem;

    h1 {
      font-size: 2.8rem;
      color: var(--black);
      text-transform: none;
      line-height: 1.3;
      font-weight: 600;
      flex: 1 1 100%;
      min-width: 0;
      overflow-wrap: anywhere;
      word-break: break-word;
      hyphens: auto;
    }

    h1::first-letter { text-transform: uppercase; }
  }

  .post-controls {
    display: flex;
    gap: 0.6rem;
    flex-wrap: wrap;
    flex-shrink: 0;

    .control-btn {
      background: var(--purple-soft);
      color: var(--purple);
      padding: 0.5rem 1rem;
      border: none;
      border-radius: var(--radius-sm);
      font-size: 1.1rem;
      cursor: pointer;
      font-family: inherit;
      text-transform: none;
      display: inline-flex;
      align-items: center;
      gap: 0.4rem;
      transition: background 0.15s;

      &:hover { background: var(--purple-hover); }
      &:disabled { opacity: 0.5; cursor: wait; }

      i { font-size: 1rem; }

      &.danger {
        background: rgba(163, 45, 45, 0.1);
        color: #A32D2D;
        &:hover { background: rgba(163, 45, 45, 0.2); }
      }
    }
  }

  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    max-width: 100%;
  }

  .tag {
    background: var(--purple-soft);
    color: var(--purple);
    padding: 0.3rem 0.9rem;
    border-radius: 999px;
    font-size: 1.1rem;
    text-transform: lowercase;
    max-width: 100%;
    overflow-wrap: anywhere;
    word-break: break-word;
  }

  .content {
    font-size: 1.5rem;
    line-height: 1.8;
    color: var(--black);
    text-transform: none;
    white-space: pre-wrap;
    margin-bottom: 2rem;
    /* CRITICAL — multiple defenses against horizontal overflow.
       Some browsers / nesting contexts ignore overflow-wrap alone;
       word-break: break-all is the most aggressive fallback. */
    overflow-wrap: anywhere;
    word-break: break-word;
    hyphens: auto;
    max-width: 100%;
    overflow-x: hidden;
    min-width: 0;
  }

  .post-actions {
    padding: 1.5rem 0;
    border-top: var(--border);
    border-bottom: var(--border);

    .like-btn {
      background: transparent;
      cursor: pointer;
      font-size: 1.4rem;
      color: var(--light-color);
      font-family: inherit;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.6rem 1rem;
      border-radius: var(--radius-sm);
      transition: background 0.15s, color 0.15s;

      i { font-size: 1.6rem; }

      &:hover {
        background: rgba(163, 45, 45, 0.05);
        color: #A32D2D;
      }
      &.liked { color: #A32D2D; }
    }
  }
}

@media (max-width: 768px) {
  .post-full {
    padding: 1.5rem;
    border-radius: var(--radius-sm);
  }
  .post-full .cover-image { margin: -1.5rem -1.5rem 1.5rem; }
  .post-full h1 { font-size: 2.2rem; }
  .post-header { flex-direction: column; }
  .post-controls { width: 100%; }
}
</style>
