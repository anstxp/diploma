<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <div class="page-head">
      <h1 class="page-title">{{ $t('blog.listTitle') }}</h1>
      <router-link v-if="isAuth" to="/blog/new" class="btn">
        <i class="fa-solid fa-plus"></i> {{ $t('blog.createPostButton') }}
      </router-link>
    </div>

    <div v-if="loading" class="loader">{{ $t('blog.loading') }}</div>

    <div v-else-if="posts.length === 0" class="empty-state">
      <i class="fa-solid fa-book-open"></i>
      <p>{{ $t('blog.emptyText') }}</p>
    </div>

    <div v-else class="posts-grid">
      <BlogPostCard v-for="p in posts" :key="p.id" :post="p" />
    </div>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import BlogPostCard from "@/components/blog-components/blog-post-card.vue";

export default {
  name: "BlogPostsView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent, BlogPostCard },
  data() { return { loading: false }; },
  computed: {
    posts() { return this.$store.state.blog.posts; },
    isAuth() { return this.$store.state.auth.isAuth; },
  },
  async mounted() {
    this.loading = true;
    try {
      await this.$store.dispatch("blog/loadPosts", { pageSize: 20 });
    } finally {
      this.loading = false;
    }
  },
};
</script>

<style scoped lang="scss">
.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 2rem;
}

.posts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(32rem, 1fr));
  gap: 1.6rem;
}
</style>
