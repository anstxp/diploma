<template>
  <BottomNavbarComponent />
  <HeaderComponent />
  <NavbarComponent />

  <main class="page invite-page">
    <div v-if="loading" class="loader">{{ $t('invite.loadingTitle') }}</div>

    <div v-else-if="!isAuth" class="not-auth-block">
      <i class="fa-solid fa-lock"></i>
      <h2>{{ $t('invite.notAuthTitle') }}</h2>
      <p>{{ $t('invite.notAuthText') }}</p>
      <div class="actions">
        <router-link :to="signInRoute" class="btn">{{ $t('nav.signIn') }}</router-link>
        <router-link :to="signUpRoute" class="btn-outline">{{ $t('nav.signUp') }}</router-link>
      </div>
    </div>

    <div v-else-if="!invite" class="empty-state">
      <i class="fa-solid fa-circle-exclamation"></i>
      <p>{{ $t('invite.emptyTitle') }}</p>
      <p class="muted">{{ $t('invite.emptySubtitle') }}</p>
      <router-link to="/" class="btn">{{ $t('common.goHome') }}</router-link>
    </div>

    <div v-else-if="alreadyResponded" class="invite-card">
      <div class="invite-head">
        <i class="fa-solid fa-circle-check" v-if="invite.status === 'Accepted'"></i>
        <i class="fa-solid fa-circle-xmark" v-else></i>
        <h2 v-if="invite.status === 'Accepted'">{{ $t('invite.acceptedTitle') }}</h2>
        <h2 v-else>{{ $t('invite.declinedTitle') }}</h2>
      </div>
      <p class="invite-subtitle" v-html="alreadyRespondedSubtitle"></p>
      <div class="actions">
        <button
          v-if="invite.status === 'Accepted'"
          class="btn-danger"
          @click="onRevoke"
          :disabled="processing"
        >
          <i class="fa-solid fa-user-slash"></i> {{ $t('invite.revokeButton') }}
        </button>
        <router-link to="/user-home" class="btn">{{ $t('nav.myDashboard') }}</router-link>
        <router-link to="/" class="btn-outline">{{ $t('common.goHome') }}</router-link>
      </div>
    </div>

    <div v-else class="invite-card">
      <div class="invite-head">
        <i class="fa-solid fa-user-doctor"></i>
        <h2>{{ $t('invite.cardTitle') }}</h2>
      </div>

      <div class="doctor-card">
        <div class="doctor-avatar">{{ doctorInitials }}</div>
        <div class="doctor-info">
          <div class="doctor-name">{{ invite.doctorName || $t('invite.doctorFallback') }}</div>
          <div class="doctor-role">{{ $t('invite.doctorRole') }}</div>
          <div class="invited-at">{{ $t('invite.invitedAt', { date: formattedDate }) }}</div>
        </div>
      </div>

      <div v-if="invite.inviteMessage" class="invite-message">
        <h4>{{ $t('invite.messageFromDoctor') }}</h4>
        <p>{{ invite.inviteMessage }}</p>
      </div>

      <div class="info-block">
        <h4>{{ $t('invite.whatThisMeans') }}</h4>
        <p>{{ $t('invite.whatThisMeansText') }}</p>
        <p>{{ $t('invite.canRevoke') }}</p>
      </div>

      <div class="actions">
        <button class="btn-danger" @click="onDecline" :disabled="processing">
          <i class="fa-solid fa-xmark"></i> {{ $t('invite.declineButton') }}
        </button>
        <button class="btn" @click="onAccept" :disabled="processing">
          <i class="fa-solid fa-check"></i>
          {{ processing ? $t('common.processing') : $t('invite.acceptButton') }}
        </button>
      </div>
    </div>
  </main>

  <FooterComponent />
</template>

<script>
import HeaderComponent from "@/components/nav-components/header/header-component.vue";
import NavbarComponent from "@/components/nav-components/navbar/navbar-component.vue";
import FooterComponent from "@/components/nav-components/footer/footer-component.vue";
import BottomNavbarComponent from "@/components/nav-components/bottom-navbar/bottom-navbar-component.vue";
import patientsApi from "@/api/patients";

export default {
  name: "InviteResponseView",
  components: { HeaderComponent, NavbarComponent, FooterComponent, BottomNavbarComponent },
  data() {
    return {
      loading: true,
      processing: false,
      invite: null,
    };
  },
  computed: {
    isAuth() { return this.$store.state.auth.isAuth; },
    linkId() { return this.$route.params.linkId; },
    signInRoute() {
      return { path: "/sign-in", query: { redirect: this.$route.fullPath } };
    },
    signUpRoute() {
      return { path: "/sign-up", query: { redirect: this.$route.fullPath } };
    },
    alreadyResponded() {
      return this.invite && ["Accepted", "Declined", "Revoked"].includes(this.invite.status);
    },
    doctorInitials() {
      const n = this.invite?.doctorName || "";
      const parts = n.split(" ").filter(Boolean);
      return ((parts[0]?.[0] || "") + (parts[1]?.[0] || "")).toUpperCase() || "Л";
    },
    formattedDate() {
      if (!this.invite?.createdAt) return "";
      const lang = this.$locale === 'en' ? 'en-US' : 'uk-UA';
      return new Date(this.invite.createdAt).toLocaleDateString(lang, {
        day: "numeric", month: "long", year: "numeric",
      });
    },
    formattedRespondedAt() {
      if (!this.invite?.respondedAt) return "";
      const d = new Date(this.invite.respondedAt);
      const lang = this.$locale === 'en' ? 'en-US' : 'uk-UA';
      return d.toLocaleDateString(lang, { day: "numeric", month: "long" });
    },
    alreadyRespondedSubtitle() {
      const key = this.invite.status === 'Accepted'
        ? 'invite.acceptedSubtitle'
        : 'invite.declinedSubtitle';
      const doctor = this.escapeHtml(this.invite.doctorName || this.$t('invite.doctorFallback'));
      return this.$t(key, {
        doctor: `<strong>${doctor}</strong>`,
        when: this.escapeHtml(this.formattedRespondedAt),
      });
    },
  },
  async mounted() {
    if (!this.isAuth) {
      this.loading = false;
      return;
    }
    await this.loadInvite();
  },
  methods: {
    escapeHtml(s) {
      return String(s || "")
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
    },
    async loadInvite() {
      this.loading = true;
      try {
        const { data } = await patientsApi.myDoctors();
        const list = data.items || data || [];
        this.invite = list.find((l) => l.id === this.linkId) || null;
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: this.$t('invite.errorLoad'),
        });
      } finally {
        this.loading = false;
      }
    },
    async onAccept() {
      this.processing = true;
      try {
        await patientsApi.respond(this.linkId, true);
        this.$store.dispatch("flash", {
          type: "success",
          message: this.$t('invite.successAccept'),
        });
        await this.loadInvite();
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('invite.errorAccept'),
        });
      } finally {
        this.processing = false;
      }
    },
    async onDecline() {
      if (!confirm(this.$t('invite.declineConfirm'))) return;
      this.processing = true;
      try {
        await patientsApi.respond(this.linkId, false);
        this.$store.dispatch("flash", {
          type: "success",
          message: this.$t('invite.successDecline'),
        });
        await this.loadInvite();
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('invite.errorDecline'),
        });
      } finally {
        this.processing = false;
      }
    },
    async onRevoke() {
      if (!confirm(this.$t('invite.revokeConfirm'))) return;
      this.processing = true;
      try {
        await patientsApi.removeLink(this.linkId, null);
        this.$store.dispatch("flash", {
          type: "success",
          message: this.$t('invite.successRevoke'),
        });
        await this.loadInvite();
      } catch (e) {
        this.$store.dispatch("flash", {
          type: "error",
          message: e.response?.data?.detail || this.$t('invite.errorRevoke'),
        });
      } finally {
        this.processing = false;
      }
    },
  },
};
</script>

<style scoped lang="scss">
.invite-page {
  min-height: calc(100vh - 26rem);
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding-top: 4rem;
}

.invite-card,
.not-auth-block,
.empty-state {
  background: white;
  border: var(--border);
  border-radius: 0.6rem;
  padding: 3rem;
  width: 100%;
  max-width: 60rem;
  box-shadow: var(--box-shadow);
}

.not-auth-block,
.empty-state {
  text-align: center;

  i {
    font-size: 4.6rem;
    color: var(--purple);
    margin-bottom: 1.5rem;
  }

  h2 {
    font-size: 2.2rem;
    color: var(--black);
    margin-bottom: 0.8rem;
    font-weight: 600;
    text-transform: none;
  }

  p {
    font-size: 1.4rem;
    color: var(--light-color);
    line-height: 1.6;
    margin-bottom: 1rem;
    text-transform: none;
  }

  .muted {
    font-size: 1.2rem;
    margin-bottom: 1.5rem;
  }

  .actions {
    margin-top: 1.5rem;
    display: flex;
    justify-content: center;
    gap: 1rem;
    flex-wrap: wrap;
  }
}

.invite-head {
  text-align: center;
  margin-bottom: 2rem;

  i {
    font-size: 4rem;
    color: var(--purple);
    margin-bottom: 1rem;

    &.fa-circle-check { color: #3B6D11; }
    &.fa-circle-xmark { color: #A32D2D; }
  }

  h2 {
    font-size: 2.4rem;
    color: var(--black);
    text-transform: none;
    font-weight: 600;
  }
}

.invite-subtitle {
  text-align: center;
  font-size: 1.4rem;
  color: var(--light-color);
  text-transform: none;
  line-height: 1.6;
  margin-bottom: 2rem;

  :deep(strong) { color: var(--black); }
}

.doctor-card {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.5rem;
  background: rgba(65, 90, 119, 0.05);
  border-radius: 0.5rem;
  margin-bottom: 1.5rem;

  .doctor-avatar {
    width: 6rem;
    height: 6rem;
    border-radius: 50%;
    background: var(--purple);
    color: white;
    font-weight: 600;
    font-size: 2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .doctor-info { flex: 1; min-width: 0; }

  .doctor-name {
    font-size: 1.7rem;
    font-weight: 600;
    color: var(--black);
    margin-bottom: 0.3rem;
    text-transform: none;
  }

  .doctor-role {
    font-size: 1.2rem;
    color: var(--purple);
    text-transform: lowercase;
    margin-bottom: 0.4rem;
    letter-spacing: 0.05rem;
  }

  .invited-at {
    font-size: 1.2rem;
    color: var(--light-color);
    text-transform: none;
  }
}

.invite-message,
.info-block {
  margin: 1.5rem 0;

  h4 {
    font-size: 1.3rem;
    text-transform: uppercase;
    color: var(--purple);
    letter-spacing: 0.1rem;
    font-weight: 600;
    margin-bottom: 0.7rem;
  }

  p {
    font-size: 1.4rem;
    line-height: 1.7;
    color: var(--black);
    text-transform: none;
    margin-bottom: 0.7rem;

    strong { color: var(--purple); }
  }
}

.invite-message {
  padding: 1.4rem;
  background: rgba(65, 90, 119, 0.05);
  border-left: 0.4rem solid var(--purple);
  border-radius: 0 0.4rem 0.4rem 0;
}

.info-block {
  padding-top: 1rem;
  border-top: var(--border);
}

.actions {
  display: flex;
  gap: 1rem;
  margin-top: 2rem;
  justify-content: center;
  flex-wrap: wrap;

  .btn, .btn-outline, .btn-danger {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    min-width: 14rem;
    justify-content: center;

    &:disabled {
      opacity: 0.5;
      cursor: not-allowed;
    }
  }
}
</style>
