<template>
  <section class="newsletter">
    <div class="form-container">
      <h3>{{ $t('landing.newsletter.title') }}</h3>
      <p>{{ $t('landing.newsletter.body') }}</p>
      <router-link
        :to="isAuth ? '/analyses/new' : '/sign-up'"
        class="btn"
      >{{ isAuth ? $t('landing.newsletter.ctaAuth') : $t('landing.newsletter.ctaGuest') }}</router-link>
    </div>
  </section>
</template>

<script>
export default {
  name: "NewsletterComponent",
  computed: {
    isAuth() { return this.$store.state.auth.isAuth; },
  },
};
</script>

<style scoped lang="scss">
.newsletter {
  background: var(--purple);
  padding: 5rem 9%;
  text-align: center;

  .form-container { max-width: 60rem; margin: 0 auto; }

  h3 {
    font-size: 2.6rem;
    color: white;
    margin-bottom: 1rem;
    text-transform: none;
    font-weight: 500;
  }

  p {
    font-size: 1.4rem;
    color: rgba(255,255,255,0.85);
    line-height: 1.7;
    text-transform: none;
    margin-bottom: 1rem;
  }

  .btn {
    background: white;
    color: var(--purple);
    font-weight: 600;
    margin-top: 1.5rem;

    &:hover { background: var(--black); color: white; }
  }
}

@media (max-width: 768px) {
  .newsletter { padding: 3rem 5%; }
}
</style>
