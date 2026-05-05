<template>
  <article class="post-card">
    <router-link :to="`/blog/${post.id}`" class="cover-link" v-if="post.coverImageUrl">
      <img :src="post.coverImageUrl" :alt="post.title" class="cover-thumb" />
    </router-link>
    <router-link :to="`/blog/${post.id}`" class="title">{{ post.title }}</router-link>
    <div class="meta">
      <span><i class="fa-solid fa-user"></i> {{ post.authorName || $t('blog.anonymous') }}</span>
      <span><i class="fa-solid fa-clock"></i> {{ formatDate(post.createdAt) }}</span>
    </div>
    <p class="excerpt">{{ excerpt }}</p>
    <div class="tags" v-if="post.tags">
      <span v-for="t in tagsList" :key="t" class="tag">#{{ t }}</span>
    </div>
    <div class="actions">
      <button class="like" :class="{ liked: post.isLiked }" @click.prevent="toggleLike">
        <i class="fa-solid fa-heart"></i> {{ post.likesCount || 0 }}
      </button>
      <span class="comments">
        <i class="fa-solid fa-comment"></i> {{ post.commentsCount || 0 }}
      </span>
    </div>
  </article>
</template>

<script>
export default {
  name: "BlogPostCard",
  props: {
    post: { type: Object, required: true },
  },
  computed: {
    excerpt() {
      const c = this.post.excerpt || this.post.content || "";
      return c.length > 200 ? c.slice(0, 200) + "…" : c;
    },
    tagsList() {
      if (!this.post.tags) return [];
      return Array.isArray(this.post.tags)
        ? this.post.tags
        : String(this.post.tags).split(",").map((s) => s.trim()).filter(Boolean);
    },
  },
  methods: {
    formatDate(iso) {
      if (!iso) return "";
      const lang = this.$locale === "en" ? "en-US" : "uk-UA";
      return new Date(iso).toLocaleDateString(lang, {
        day: "numeric", month: "short", year: "numeric",
      });
    },
    async toggleLike() {
      if (!this.$store.state.auth.isAuth) {
        this.$router.push("/sign-in");
        return;
      }
      try {
        await this.$store.dispatch("blog/like", this.post.id);
      } catch (e) {
        this.$store.dispatch("flash", { type: "error", message: this.$t('blog.likeError') });
      }
    },
  },
};
</script>

<style scoped lang="scss">
.post-card {
  background: var(--surface);
  border: var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
  min-width: 0;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;

  &:hover {
    border-color: rgba(0, 0, 0, 0.15);
    box-shadow: var(--shadow);
    transform: translateY(-2px);

    .cover-thumb { transform: scale(1.04); }
    .title { color: var(--purple); }
  }

  .cover-link {
    display: block;
    aspect-ratio: 16 / 9;
    background: var(--purple-soft);
    overflow: hidden;
  }

  .cover-thumb {
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s ease;
    display: block;
  }

  .title {
    display: block;
    font-size: 1.8rem;
    color: var(--black);
    font-weight: 600;
    margin: 1.8rem 1.8rem 0.6rem;
    text-transform: none;
    line-height: 1.35;
    overflow-wrap: anywhere;
    word-break: break-word;
    hyphens: auto;
    transition: color 0.18s ease;
  }

  .title::first-letter { text-transform: uppercase; }

  .meta {
    display: flex;
    flex-wrap: wrap;
    gap: 1.5rem;
    font-size: 1.15rem;
    color: var(--light-color);
    margin: 0 1.8rem 1.2rem;
    text-transform: none;

    i { color: var(--purple); margin-right: 0.4rem; }
  }

  .excerpt {
    font-size: 1.35rem;
    line-height: 1.65;
    color: var(--light-color);
    margin: 0 1.8rem 1.2rem;
    text-transform: none;
    overflow-wrap: anywhere;
    word-break: break-word;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .excerpt::first-letter { text-transform: uppercase; }

  .tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin: 0 1.8rem 1rem;
    max-width: calc(100% - 3.6rem);
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

  .actions {
    display: flex;
    gap: 1.5rem;
    align-items: center;
    padding: 1rem 1.8rem 1.6rem;
    border-top: var(--border);
    margin-top: auto;  /* push to bottom of card */
    background: var(--surface-2);

    button.like {
      background: transparent;
      cursor: pointer;
      font-size: 1.3rem;
      color: var(--light-color);
      font-family: inherit;
      display: inline-flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.4rem 0.8rem;
      border-radius: var(--radius-sm);
      transition: background 0.15s ease, color 0.15s ease;

      i { font-size: 1.4rem; }

      &:hover {
        color: #A32D2D;
        background: rgba(163, 45, 45, 0.06);
      }
      &.liked { color: #A32D2D; }
    }

    .comments {
      font-size: 1.3rem;
      color: var(--light-color);
      display: inline-flex;
      align-items: center;
      gap: 0.3rem;

      i { color: var(--purple); }
    }
  }
}
</style>
