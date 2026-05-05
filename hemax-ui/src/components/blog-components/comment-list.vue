<template>
  <div class="comments">
    <h4>{{ $t('blog.comments.headerLabel') }} ({{ comments.length }})</h4>

    <div v-if="isAuth" class="add-comment">
      <textarea
        v-model="newComment"
        rows="3"
        :placeholder="$t('blog.comments.placeholder')"
        class="box"
      ></textarea>
      <button
        class="btn-small"
        @click="onAdd"
        :disabled="!newComment.trim() || sending"
      >
        {{ sending ? $t('blog.comments.sending') : $t('blog.comments.submitButton') }}
      </button>
    </div>
    <div v-else class="add-comment-prompt">
      <router-link to="/sign-in">{{ $t('blog.comments.promptSignInLink') }}</router-link>{{ $t('blog.comments.promptSignInSuffix') }}
    </div>

    <div class="list">
      <div v-for="c in comments" :key="c.id" class="comment">
        <div class="avatar">{{ initials(c.authorName) }}</div>
        <div class="body">
          <div class="head">
            <span class="name">{{ c.authorName || $t('blog.comments.anonymous') }}</span>
            <span class="time">{{ formatTime(c.createdAt) }}</span>
          </div>
          <p>{{ c.content }}</p>
        </div>
      </div>
      <div v-if="!comments.length" class="empty">
        <i class="fa-solid fa-comment-slash"></i>
        <span>{{ $t('blog.comments.emptyText') }}</span>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: "CommentList",
  props: {
    postId: { type: String, required: true },
    comments: { type: Array, default: () => [] },
  },
  data() {
    return { newComment: "", sending: false };
  },
  computed: {
    isAuth() { return this.$store.state.auth.isAuth; },
  },
  methods: {
    initials(name) {
      if (!name) return "?";
      return name.split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();
    },
    formatTime(iso) {
      if (!iso) return "";
      const lang = this.$locale === "en" ? "en-US" : "uk-UA";
      return new Date(iso).toLocaleString(lang, { dateStyle: "short", timeStyle: "short" });
    },
    async onAdd() {
      if (!this.newComment.trim()) return;
      this.sending = true;
      try {
        await this.$store.dispatch("blog/addComment", {
          postId: this.postId,
          content: this.newComment.trim(),
        });
        this.newComment = "";
      } catch {
        this.$store.dispatch("flash", { type: "error", message: this.$t('blog.comments.addError') });
      } finally {
        this.sending = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
.comments {
  margin-top: 2rem;

  h4 {
    font-size: 1.4rem;
    text-transform: uppercase;
    color: var(--purple);
    letter-spacing: 0.1rem;
    margin-bottom: 1rem;
    font-weight: 600;
  }
}

.add-comment {
  margin-bottom: 1.5rem;

  .box {
    width: 100%;
    padding: 1rem;
    font-size: 1.4rem;
    border: var(--border);
    border-radius: 0.4rem;
    text-transform: none;
    margin-bottom: 0.5rem;
    resize: vertical;

    &:focus { border-color: var(--purple); }
  }
}

.add-comment-prompt {
  padding: 1.5rem;
  background: rgba(65, 90, 119, 0.05);
  border-radius: 0.4rem;
  font-size: 1.3rem;
  color: var(--light-color);
  text-align: center;
  text-transform: none;
  margin-bottom: 1.5rem;

  a {
    color: var(--purple);
    text-decoration: underline;
    font-weight: 500;
  }
}

.comment {
  display: flex;
  gap: 1rem;
  padding: 1.2rem 0;
  border-bottom: 1px solid rgba(0,0,0,0.05);

  .avatar {
    width: 3.6rem;
    height: 3.6rem;
    border-radius: 50%;
    background: var(--purple);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 600;
    font-size: 1.2rem;
    flex-shrink: 0;
  }

  .body { flex: 1; }

  .head {
    display: flex;
    gap: 1rem;
    align-items: baseline;
    margin-bottom: 0.4rem;

    .name {
      font-size: 1.3rem;
      font-weight: 600;
      color: var(--black);
      text-transform: none;
    }
    .time {
      font-size: 1.1rem;
      color: var(--light-color);
      text-transform: none;
    }
  }

  p {
    font-size: 1.3rem;
    color: var(--black);
    line-height: 1.6;
    text-transform: none;
  }
}

.empty {
  padding: 2rem;
  text-align: center;
  color: var(--light-color);
  font-size: 1.3rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  align-items: center;

  i { font-size: 2rem; }
}
</style>
