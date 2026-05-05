<template>
  <section class="contacts">
    <div class="heading"><span>{{ $t('contacts.heading') }}</span></div>

    <div class="contacts-grid">
      <div class="contact-card">
        <i class="fa-solid fa-envelope"></i>
        <h4>{{ $t('contacts.emailTitle') }}</h4>
        <a href="mailto:hello@hemax.local">hello@hemax.local</a>
      </div>
      <div class="contact-card">
        <i class="fa-solid fa-phone"></i>
        <h4>{{ $t('contacts.phoneTitle') }}</h4>
        <a href="tel:+380000000000">+380 XX XXX XX XX</a>
      </div>
      <div class="contact-card">
        <i class="fa-solid fa-location-dot"></i>
        <h4>{{ $t('contacts.addressTitle') }}</h4>
        <p>{{ $t('contacts.addressText') }}</p>
      </div>
      <div class="contact-card">
        <i class="fa-solid fa-clock"></i>
        <h4>{{ $t('contacts.supportTitle') }}</h4>
        <p>{{ $t('contacts.supportText') }}</p>
      </div>
    </div>

    <div class="form-wrap">
      <form class="contact-form" @submit.prevent="onSubmit">
        <h3>{{ $t('contacts.formTitle') }}</h3>
        <div class="form-row">
          <span>{{ $t('contacts.nameLabel') }}</span>
          <input v-model="form.name" type="text" class="box" :placeholder="$t('contacts.namePlaceholder')" />
        </div>
        <div class="form-row">
          <span>{{ $t('contacts.emailLabel') }}</span>
          <input v-model="form.email" type="email" class="box" placeholder="your@email.com" />
        </div>
        <div class="form-row">
          <span>{{ $t('contacts.messageLabel') }}</span>
          <textarea v-model="form.message" class="box" rows="5" :placeholder="$t('contacts.messagePlaceholder')"></textarea>
        </div>
        <button type="submit" class="btn">{{ $t('contacts.submitButton') }}</button>
      </form>
    </div>
  </section>
</template>

<script>
export default {
  name: "ContactsComponent",
  data() {
    return { form: { name: "", email: "", message: "" } };
  },
  methods: {
    onSubmit() {
      this.$store.dispatch("flash", {
        type: "success",
        message: this.$t('contacts.successFlash'),
      });
      this.form = { name: "", email: "", message: "" };
    },
  },
};
</script>

<style scoped lang="scss">
.contacts {
  padding: 4rem 9%;

  .contacts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr));
    gap: 1.6rem;
    margin-bottom: 3rem;
  }

  .contact-card {
    background: white;
    border: var(--border);
    border-radius: .6rem;
    padding: 2rem;
    text-align: center;

    i { font-size: 2.4rem; color: var(--purple); margin-bottom: 1rem; }

    h4 {
      font-size: 1.4rem;
      color: var(--black);
      margin-bottom: 0.6rem;
      text-transform: uppercase;
      letter-spacing: 0.05rem;
    }

    a, p {
      font-size: 1.3rem;
      color: var(--light-color);
      text-transform: none;
    }

    a:hover { color: var(--purple); }
  }

  .form-wrap { display: flex; justify-content: center; }

  .contact-form {
    width: 100%;
    max-width: 60rem;
    background: white;
    border: var(--border);
    border-radius: .6rem;
    padding: 2rem;

    h3 {
      font-size: 2rem;
      text-transform: uppercase;
      color: var(--black);
      margin-bottom: 1rem;
      letter-spacing: 0.05rem;
    }
  }
}

@media (max-width: 768px) {
  .contacts { padding: 3rem 5%; }
}
</style>
