<template>
  <footer class="footer">
    <div class="box-container">
      <div class="box">
        <h3>{{ $t('footer.aboutTitle') }}</h3>
        <p class="about">{{ $t('footer.aboutText') }}</p>
      </div>

      <div class="box">
        <h3>{{ $t('footer.quickLinksTitle') }}</h3>
        <router-link to="/"><i class="fa-solid fa-arrow-right"></i> {{ $t('nav.home') }}</router-link>
        <router-link to="/blog"><i class="fa-solid fa-arrow-right"></i> {{ $t('nav.blog') }}</router-link>
        <router-link to="/contacts"><i class="fa-solid fa-arrow-right"></i> {{ $t('nav.contacts') }}</router-link>
        <router-link to="/faq"><i class="fa-solid fa-arrow-right"></i> {{ $t('nav.faq') }}</router-link>
      </div>

      <div class="box">
        <h3>{{ $t('footer.securityTitle') }}</h3>
        <p class="about">{{ $t('footer.securityText') }}</p>
      </div>

      <div class="box">
        <h3>{{ $t('footer.contactsTitle') }}</h3>
        <a href="mailto:hello@hemax.local"><i class="fa-solid fa-envelope"></i> hello@hemax.local</a>
        <a href="tel:+380XXXXXXXXX"><i class="fa-solid fa-phone"></i> +380 XX XXX XX XX</a>
      </div>
    </div>

    <div class="share">
      <a href="#" class="fab fa-github"></a>
      <a href="#" class="fab fa-linkedin"></a>
      <a href="#" class="fab fa-telegram"></a>
    </div>

    <div class="credit">
      {{ $t('footer.credit', { year }) }}
    </div>
  </footer>
</template>

<script>
export default {
  name: "FooterComponent",
  computed: {
    year() { return new Date().getFullYear(); },
  },
};
</script>

<style scoped lang="scss">
@import "footer-style";
</style>
