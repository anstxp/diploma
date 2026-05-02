<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page">
    <div class="page-head">
      <h1 class="page-title">{{ $t('patients.pageTitle') }}</h1>
      <button class="btn" @click="showInvite = !showInvite">
        <i class="fa-solid fa-plus"></i> {{ $t('patients.invitePatientButton') }}
      </button>
    </div>

    <div v-if="showInvite" class="invite-form">
      <div class="row">
        <span>{{ $t('patients.emailLabel') }}</span>
        <input v-model="invite.email" type="email" class="box" :placeholder="$t('patients.emailPlaceholder')" />
      </div>
      <div class="row">
        <span>{{ $t('patients.messageLabel') }}</span>
        <textarea v-model="invite.message" class="box" rows="3" :placeholder="$t('patients.messagePlaceholder')"></textarea>
      </div>
      <div class="invite-actions">
        <button class="btn-outline btn-small" @click="showInvite = false">{{ $t('patients.inviteCancel') }}</button>
        <button class="btn btn-small" @click="onInvite" :disabled="!invite.email || sending">
          {{ sending ? $t('patients.inviteSending') : $t('patients.inviteSend') }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="loader">{{ $t('patients.loading') }}</div>

    <div v-else-if="patients.length === 0" class="empty-state">
      <i class="fa-solid fa-users"></i>
      <p>{{ $t('patients.emptyText') }}</p>
    </div>

    <div v-else class="patients-list">
      <PatientCard
        v-for="p in patients"
        :key="p.linkId || p.userId"
        :patient="p"
        @accept="onRespond($event, true)"
        @decline="onRespond($event, false)"
        @revoke="onRevoke($event)"
      />
    </div>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import PatientCard from "@/components/patient-components/patient-card.vue";

export default {
  name: "PatientsView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent, PatientCard },
  data() {
    return {
      loading: false,
      sending: false,
      showInvite: false,
      invite: { email: "", message: "" },
    };
  },
  computed: {
    patients() { return this.$store.state.patients.list; },
  },
  async mounted() {
    this.loading = true;
    try {
      await this.$store.dispatch("patients/loadMyPatients");
    } finally {
      this.loading = false;
    }
  },
  methods: {
    async onInvite() {
      if (!this.invite.email) return;
      this.sending = true;
      try {
        await this.$store.dispatch("patients/invite", { ...this.invite });
        this.$store.dispatch("flash", { type: "success", message: this.$t('patients.inviteSuccessFlash') });
        this.invite = { email: "", message: "" };
        this.showInvite = false;
        await this.$store.dispatch("patients/loadMyPatients");
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('patients.inviteErrorFlash'),
        });
      } finally {
        this.sending = false;
      }
    },
    async onRespond(linkId, accepted) {
      try {
        await this.$store.dispatch("patients/respond", { linkId, accepted });
        await this.$store.dispatch("patients/loadMyPatients");
      } catch (e) {
        this.$store.dispatch("flash", { type: "error", message: this.$t('patients.inviteErrorFlash') });
      }
    },
    async onRevoke(linkId) {
      if (!window.confirm(this.$t('patients.card.revokeConfirm'))) return;
      try {
        await this.$store.dispatch("patients/revoke", { linkId });
        await this.$store.dispatch("patients/loadMyPatients");
      } catch (e) {
        this.$store.dispatch("flash", { type: "error", message: this.$t('patients.inviteErrorFlash') });
      }
    },
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

  .btn { display: inline-flex; align-items: center; gap: 0.5rem; }
}

.invite-form {
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 1.5rem;
  margin-bottom: 2rem;

  .row { margin-bottom: 1rem; }
  .row > span {
    display: block;
    font-size: 1.3rem;
    color: var(--black);
    margin-bottom: 0.4rem;
    text-transform: lowercase;
  }
  .box {
    width: 100%;
    padding: 0.8rem 1.2rem;
    font-size: 1.4rem;
    border: var(--border);
    border-radius: 0.5rem;
    text-transform: none;
    resize: vertical;

    &:focus { border-color: var(--purple); }
  }
}

.invite-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.patients-list { display: flex; flex-direction: column; gap: 1rem; }
</style>
